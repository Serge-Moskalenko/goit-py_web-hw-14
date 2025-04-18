from fastapi import APIRouter, HTTPException, Depends, status, Request, Response,BackgroundTasks,Form
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse, HTMLResponse

from src.database.db import get_db
from src.repository import users as repositories_users
from src.schemas.user import RequestEmail, ResetPasswordSchema, UserSchema, TokenSchema, UserResponse
from src.services.auth import auth_service
from src.services.email import send_email, send_reset_password_email

router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema,bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login",  response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    access_token = await auth_service.create_access_token(data={"sub": user.email, "test": "Сергій Багмет"})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)

    auth_service.cache_user(user.email, user)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token',  response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    print(token)
    email = await auth_service.decode_refresh_token(token)
    print(email)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get('/check-email-open/{username}')
async def request_email(username: str, response: Response, db: AsyncSession = Depends(get_db)):
    print('--------------------------------')
    print(f'{username} зберігаємо що він відкрив email в БД')
    print('--------------------------------')
    return FileResponse("src/static/open_check.png", media_type="image/png", content_disposition_type="inline")

@router.get("/confirmed_email/{token}", response_class=HTMLResponse)
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    try:
        email = await auth_service.get_email_from_token(token)
        user = await repositories_users.get_user_by_email(email, db)
        if user and not user.confirmed:
            user.confirmed = True
            await db.commit()
            return HTMLResponse(content="<h2>Email confirmed successfully!</h2>", status_code=200)
        return HTMLResponse(content="<h3>Email already confirmed or user not found.</h3>", status_code=400)
    except Exception as e:
        print(e)
        return HTMLResponse(content="<h3>Invalid or expired token.</h3>", status_code=400)
    
@router.post("/request-reset-password")
async def request_password_reset(user_data: RequestEmail , request: Request, db: AsyncSession = Depends(get_db)):
    user = await repositories_users.get_user_by_email(user_data.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    host = str(request.base_url)
    await send_reset_password_email(user.email, user.username, host)
    return {"message": "Password reset email sent"}

@router.post("/reset-password")
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    email = await auth_service.verify_password_reset_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    hashed_password = auth_service.get_password_hash(new_password)
    await repositories_users.update_user_password(user.email, hashed_password, db)
    return {"message": "Password updated successfully"}


@router.get("/reset-password-page", response_class=HTMLResponse)
async def reset_password_form(token: str):
    return HTMLResponse(content=f"""
    <html>
      <body>
        <h2>Reset Your Password</h2>
        <form action="/api/auth/reset-password" method="post">
            <input type="hidden" name="token" value="{token}" />
            <label>New Password:</label>
            <input type="password" name="new_password" />
            <button type="submit">Reset</button>
        </form>
      </body>
    </html>
    """, status_code=200)