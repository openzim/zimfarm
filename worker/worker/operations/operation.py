from typing import Optional


class Operation:
    """Base class for all operations

    Attributes:
        success (:obj:`bool`, optional): task is successful or not
        std_out (:obj:`bytes`, optional): std_out
        error (:obj:`Error`, optional): error of the operation
    """

    name: str = 'Operation Base Class'

    def __init__(self):
        self.success: Optional[bool] = None
        self.std_out: Optional[bytes] = None
        self.error: Optional[Error] = None

    @property
    def log(self) -> {}:
        result = {'success': self.success, 'name': self.name}

        if self.std_out is not None:
            result['std_out'] = self.std_out.decode()
        if self.error is not None:
            result['error'] = {
                'domain': self.error.domain,
                'code': self.error.code,
                'stderr': self.error.stderr.decode() if self.error.stderr is not None else None
            }
        return result

    def execute(self):
        pass


class Error(Exception):
    """Operation Error

    Attributes:
        domain (optional): a code to identify which module produced the error
        code (optional): a code to identify the error if error occurred
        message (:obj:`str`, optional): a message to describe the error if error occurred
        stderr (:obj:`bytes`, optional): stderr
    """
    def __init__(self, domain: Optional[str], code: Optional[int]=None, message: Optional[str]=None,
                 stderr: Optional[bytes]=None):
        self.domain = domain
        self.code = code
        self.message = message
        self.stderr = stderr
