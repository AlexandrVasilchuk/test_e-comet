from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    database_url: str
    db_password: str
    db_user: str
    db_name: str
    db_host: str
    db_port: int

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Config()
