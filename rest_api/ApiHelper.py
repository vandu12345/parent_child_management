import datetime
import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from CeleryConfig import send_activation_email, send_email_to_admin
from models.DatabaseModels import Child, Parent


class ParentChildManager:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

    def __init__(self):
        # TODO: Add Logger
        self.secret_key = os.getenv("SECRET_KEY", "abcde")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        self.IMAGE_DIR = "profile_photos"
        os.makedirs(self.IMAGE_DIR, exist_ok=True)

    def get_password_hash(self, password):
        """
            This method will provide hashed password
        Args:
            password (str): Password

        Returns:
            str: Returns hashed password
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        """Verify plain password and hashed password in db

        Args:
            plain_password (_type_): _description_
            hashed_password (bool): _description_

        Returns:
            _type_: _description_
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta=None):
        """This method will create access token

        Args:
            data (dict): _description_
            expires_delta (timedelta, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.now() + expires_delta
        else:
            expire = datetime.datetime.now() + datetime.timedelta(
                minutes=self.access_token_expire_minutes
            )
        to_encode.update({"exp": expire.timestamp()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def create_parent(self, parent_details, db_session):
        """This method will create a parent if it's not exist

        Args:
            parent_details (ParentCreate): Model that contains Parent Details
            db_session (AsyncSession): Async DB Session
        """
        try:
            print("Adding New Parent")
            hashed_password = self.get_password_hash(parent_details.password)
            activation_token = self.create_access_token(
                data={"sub": parent_details.email}
            )
            parent = Parent(email=parent_details.email, hashed_password=hashed_password)
            db_session.add(parent)
            await db_session.commit()
            await db_session.refresh(parent)

            # Send Activation Link in background
            send_activation_email.apply_async(
                args=[parent_details.email, activation_token]
            )
            # send_activation_email(parent_details.email, activation_token)

        except IntegrityError as err_msg:
            print(err_msg)
            db_session.rollback()
            raise HTTPException(status_code=400, detail="Email already registered")

        except Exception as err_msg:
            print(err_msg)
            await db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong, try again",
            )

        return {
            "message": "Parent Added Successfully, For Activating your account please verify your email from email address"
        }

    async def activate_parent(self, token, db_session):
        """This method will activate parent

        Args:
            token (str): Provided token to activate account
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=self.algorithm)
            email = payload.get("sub")
            if email is None:
                raise HTTPException(status_code=400, detail="Invalid token")

            result = await db_session.execute(
                select(Parent).filter(Parent.email == email)
            )
            parent = result.scalars().first()

            if parent is None:
                raise HTTPException(status_code=404, detail="Parent not found")

            if parent.is_active:
                raise HTTPException(status_code=404, detail="Parent is already active")

            parent.is_active = True
            await db_session.commit()

        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except jwt.ExpiredSignatureError as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(status_code=400, detail="Token expired")
        except jwt.JWTError as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(status_code=400, detail="Invalid token")
        except Exception as err_msg:
            print(f"Error Occured: {err_msg}")
            await db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify Account, try again",
            )

        return {"message": "Account verified successfully"}

    async def resend_verification_email(self, email, db_session):
        """
        This method will resend verification email
        """
        try:
            parent = (
                await db_session.query(Parent).filter(Parent.email == email).first()
            )
            if parent is None:
                raise HTTPException(status_code=404, detail="Parent not found")

            if parent.is_active:
                raise HTTPException(status_code=400, detail="Account already verified")

            activation_token = self.create_access_token(data={"sub": email})
            # Send Activation Link in background
            send_activation_email.apply_async(args=[(email, activation_token)])

        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except Exception as err_msg:
            print(f"Error Occured: {err_msg}")
            await db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resend verification email, try after some time",
            )

        return {"message": "Verification email sent"}

    async def authenticate_parent(self, parent_info, db_session):
        """
        Separate method for authentication
        """
        result = await db_session.execute(
            select(Parent).filter(Parent.email == parent_info.username)
        )
        parent = result.scalars().first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not self.verify_password(parent_info.password, parent.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not parent.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not activated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return parent

    async def login_parent(self, parent_info, db_session):
        """This method will handle login of a parent

        Args:
            parent_info (ParentLogin): Contains parent info email and password
            db_session (AsyncSession): db session for query

        Raises:
            HTTPException: _description_
        """
        try:
            parent = await self.authenticate_parent(parent_info, db_session)
            access_token = self.create_access_token(data={"mail": parent.email})

        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except Exception as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify account, try again",
            )
        return {"access_token": access_token, "token_type": "bearer"}

    async def update_parent_profile(self, parent_update, profile_photo, db_session):
        """This method will update Parent profile

        Args:
            parent_update (ParentUpdate): Contains all parent info
            profile_photo (File): For Profile Photo
            db_session (AsyncSession): For Database operation
        """
        try:
            result = await db_session.execute(
                select(Parent).filter(Parent.id == parent_update.id)
            )
            parent = result.scalars().first()

            if not parent:
                raise HTTPException(status_code=404, detail="Parent not found")

            update_data = parent_update.dict(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    setattr(parent, key, value)

            if profile_photo is not None:
                # TODO: Handle different file storage
                file_location = os.path.join(
                    self.IMAGE_DIR, f"{parent_update.id}_{profile_photo.filename}"
                )
                with open(file_location, "wb") as file:
                    file.write(await profile_photo.read())
                parent.profile_photo = file_location
            await db_session.commit()
            await db_session.refresh(parent)

        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except Exception as err_msg:
            await db_session.rollback()
            print(f"Error Occured: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to Update Profile, try again",
            )

        return parent

    async def get_parent(self, id, db_session):
        """This method will Fetch Parent details

        Args:
            id (int): Id of the parent
            db_session (AsyncSession): For Database operation
        """
        try:
            result = await db_session.execute(select(Parent).filter(Parent.id == id))
            parent = result.scalars().first()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent not found")

        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except Exception as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to Fetch Parent Profile, try again",
            )

        return parent

    async def get_current_user_email(
        self, token: Annotated[str, Depends(oauth2_scheme)]
    ):
        """Get Current User

        Args:
            token (_type_): _description_
            db_session (_type_): _description_

        Raises:
            HTTPException: _description_
            HTTPException: _description_

        Returns:
            Parent: _description_
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=self.algorithm)
            email = payload.get("mail")

            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Access denied",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except jwt.ExpiredSignatureError as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(status_code=400, detail="Token expired")
        except jwt.JWTError as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(status_code=400, detail="Invalid token")
        except Exception as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed Authentication, try again",
            )

        return email

    async def get_current_user_data(self, email, db_session):
        """This method will fetch current user data

        Args:
            id (_type_): _description_
            db_session (_type_): _description_

        Raises:
            HTTPException: _description_
        """

        # TODO: Add password also otherwise different session password change will not reflect
        try:
            result = await db_session.execute(
                select(Parent.id).filter(Parent.email == email)
            )
            parent = result.scalars().first()
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except Exception as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed Authentication, try again",
            )

        return parent

    async def add_children(self, parent_id, children, db_session):
        """This method will add new children

        Args:
            parent_id (int): Parent id of the children
            children (ChildCreate): Children details
            db_session (AsyncSession): For database operations
        """
        try:
            if children.date_of_birth.tzinfo is not None:
                children.date_of_birth = children.date_of_birth.replace(tzinfo=None)
            new_child = Child(
                name=children.name,
                birth_date=children.date_of_birth,
                parent_id=parent_id,
            )
            db_session.add(new_child)
            await db_session.commit()
            await db_session.refresh(new_child)

            # Add celery task for sending email to admin
            send_email_to_admin.apply_async(args=[parent_id, children.name])

        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except Exception as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add new child , try again",
            )

        return {"message": "Child Added Successfully"}

    async def update_children(self, parent_id, children, db_session):
        """This method will Update children

        Args:
            parent_id (int): Parent id of the children
            children (ChildCreate): Children details
            db_session (AsyncSession): For database operations
        """
        try:
            if (
                children.date_of_birth is not None
                and children.date_of_birth.tzinfo is not None
            ):
                children.date_of_birth = children.date_of_birth.replace(tzinfo=None)

            result = await db_session.execute(
                select(Child).filter(Child.id == children.id)
            )
            child = result.scalars().first()
            if children.date_of_birth is not None:
                child.birth_date = children.date_of_birth

            if children.name is not None:
                child.name = children.name

            db_session.add(child)
            await db_session.commit()
            await db_session.refresh(child)

        except HTTPException as err_msg:
            print(f"Error Occured: {err_msg}")
            raise
        except Exception as err_msg:
            print(f"Error Occured: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update child , try again",
            )

        return {"message": f"Child Updated Successfully under parent {parent_id}"}

    async def list_children(self, name, added_after, added_before, db_session):
        """This method will list all the children on the basis of filter

        Args:
            name (_type_): _description_
            added_after (_type_): _description_
            added_before (_type_): _description_
            db_session (_type_): _description_
        """
        query = select(Child)

        if name:
            query = query.filter(Child.name.ilike(f"%{name}%"))
        if added_after:
            query = query.filter(Child.created_at >= added_after)
        if added_before:
            query = query.filter(Child.created_at <= added_before)

        result = await db_session.execute(query)
        children = result.scalars().all()
        return children

    async def list_children_by_parent_id(self, parent_id, db_session):
        """This method will list children for a particular parent id

        Args:
            parent_id (_type_): _description_
            db_session (_type_): _description_
        """
        result = await db_session.execute(
            select(Parent)
            .filter(Parent.id == parent_id)
            .options(selectinload(Parent.children))
        )
        parent = result.scalars().first()

        if not parent:
            raise HTTPException(status_code=404, detail="Parent not found")

        return parent
