from flask import Response


class OAuth2:
    def __call__(self, *args, **kwargs):
        print(kwargs)

        return Response()