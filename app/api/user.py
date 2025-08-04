from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from ..models.user import User
from ..db.database import get_session
from ..schemas.user import (
    UserCreate,
    UserLogin
)

# 初始化路由器
auth_router = APIRouter()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# token 相关设置
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "DxHf0N1kMa"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# 注册接口
@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, session: Session = Depends(get_session)):
    # 检查用户名是否已存在
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    # 密码哈希处理
    password_hash = pwd_context.hash(user.password)

    # 创建新用户
    db_user = User(username=user.username, password_hash=password_hash)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {"status": "success", "user_id": db_user.id}


# 登录接口
@auth_router.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    # 查询用户
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    # 验证密码
    if not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    # 创建 access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建 access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    """验证 token 并获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码 token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 查询用户
    db_user = session.exec(select(User).where(User.username == username)).first()
    if db_user is None:
        raise credentials_exception
    print(f"校验成功，{db_user}")
    return db_user


# 示例：受保护的 API 路由
@auth_router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "这是一个受保护的路由", "current_user": current_user.username}