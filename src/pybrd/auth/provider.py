class BaseAuthenticationProvider:
    REFRESH_INTERVAL = 300  # 5 minutes

    async def refresh(self):
        raise NotImplementedError()

    async def stats(self):
        raise NotImplementedError()

    async def authenticate(self, *args, **kwargs) -> bool:
        raise NotImplementedError()
