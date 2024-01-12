from pydantic import Field
from pydantic_settings import SettingsConfigDict
from utils.pydantic_advanced_settings import CustomizedSettings

__all__ = (
    'Settings',
)


class Settings(CustomizedSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    access_token: str
    gitlab_url: str
