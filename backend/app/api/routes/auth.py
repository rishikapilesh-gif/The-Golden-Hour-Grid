from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.schemas.auth import LoginRequest, LoginResponse, MeResponse, UserOut
from backend.app.services.auth_service import AuthService
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")

    auth_result = AuthService.authenticate_user(
        db=db,
        username=req.username,
        password=req.password,
        ip_address=ip,
        user_agent=ua
    )

    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your username and password."
        )

    user, token = auth_result
    redirect_to = "/ambulance" if user.role == "ambulance" else "/hospital"

    # Set secure HttpOnly session cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_TTL_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        path="/"
    )

    return LoginResponse(
        user=UserOut.model_validate(user),
        redirect_to=redirect_to
    )


@router.get("/me", response_model=MeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    redirect_to = "/ambulance" if current_user.role == "ambulance" else "/hospital"
    return MeResponse(
        user=UserOut.model_validate(current_user),
        redirect_to=redirect_to
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        AuthService.logout(db, token)

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/"
    )
    return {"message": "Logged out successfully"}
