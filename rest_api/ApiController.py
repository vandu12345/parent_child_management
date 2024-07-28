import json
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from config.Database import get_session
from models.ApiModels import (
    ChildCreate,
    ChildUpdate,
    Parent,
    ParentCreate,
    ParentLogin,
    ParentUpdate,
)
from rest_api.ApiHelper import ParentChildManager

router = APIRouter()
HelperObj = ParentChildManager()


@router.post("/register")
async def register_parent(
    parent: ParentCreate, db_session: AsyncSession = Depends(get_session)
):
    response = await HelperObj.create_parent(parent, db_session)
    return Response(content=json.dumps(response), media_type="application/json")


@router.get("/activate", response_model=dict)
async def activate_parent(token: str, db_session: AsyncSession = Depends(get_session)):
    response = await HelperObj.activate_parent(token, db_session)
    return Response(content=json.dumps(response), media_type="application/json")


@router.post("/resend-verification", response_model=dict)
async def resend_verification_email(
    email: str, db_session: AsyncSession = Depends(get_session)
):
    response = await HelperObj.resend_verification_email(email, db_session)
    return Response(content=json.dumps(response), media_type="application/json")


@router.post("/login")
async def login_for_access_token(
    parent_info: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: AsyncSession = Depends(get_session),
):
    return await HelperObj.login_parent(parent_info, db_session)


@router.put("/updateParentProfile", response_model=Parent)
async def update_parent_profile(
    current_user: Annotated[ParentLogin, Depends(HelperObj.get_current_user_email)],
    parent_update: ParentUpdate = Depends(),
    profile_photo: Optional[UploadFile] = File(None),
    db_session: AsyncSession = Depends(get_session),
):

    if (
        await HelperObj.get_current_user_data(current_user, db_session)
        != parent_update.id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this profile"
        )

    return await HelperObj.update_parent_profile(
        parent_update, profile_photo, db_session
    )


@router.get("/getParent", response_model=Parent)
async def get_parent(
    current_user: Annotated[ParentLogin, Depends(HelperObj.get_current_user_email)],
    id: int,
    db_session: AsyncSession = Depends(get_session),
):
    if await HelperObj.get_current_user_data(current_user, db_session) != id:
        raise HTTPException(
            status_code=403, detail="Not authorized to see this profile"
        )
    return await HelperObj.get_parent(id, db_session)


@router.post("/addChildren")
async def add_children(
    current_user: Annotated[ParentLogin, Depends(HelperObj.get_current_user_email)],
    children: ChildCreate,
    db_session: AsyncSession = Depends(get_session),
):
    parent_id = await HelperObj.get_current_user_data(current_user, db_session)

    if parent_id != children.parent_id:
        raise HTTPException(status_code=403, detail="Not authorized to Add Children")

    return await HelperObj.add_children(parent_id, children, db_session)


@router.put("/updateChildren")
async def update_children(
    current_user: Annotated[ParentLogin, Depends(HelperObj.get_current_user_email)],
    children_update: ChildUpdate,
    db_session: AsyncSession = Depends(get_session),
):

    parent_id = await HelperObj.get_current_user_data(current_user, db_session)
    if parent_id != children_update.parent_id:
        raise HTTPException(status_code=403, detail="Not authorized to Update Children")

    return await HelperObj.update_children(parent_id, children_update, db_session)


@router.get("/listChildren")
async def list_children(
    current_user: Annotated[ParentLogin, Depends(HelperObj.get_current_user_email)],
    parent_id: int,
    name: Optional[str] = None,
    added_after: Optional[datetime] = None,
    added_before: Optional[datetime] = None,
    db_session: AsyncSession = Depends(get_session),
):

    if await HelperObj.get_current_user_data(current_user, db_session) != parent_id:
        raise HTTPException(status_code=403, detail="Not authorized to list Children")
    return await HelperObj.list_children(name, added_after, added_before, db_session)


@router.get("/listChildrenByParentId")
async def list_children_by_parent_id(
    current_user: Annotated[ParentLogin, Depends(HelperObj.get_current_user_email)],
    parent_id: int,
    db_session: AsyncSession = Depends(get_session),
):

    if await HelperObj.get_current_user_data(current_user, db_session) != parent_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to list Parent Children relation"
        )
    return await HelperObj.list_children_by_parent_id(parent_id, db_session)
