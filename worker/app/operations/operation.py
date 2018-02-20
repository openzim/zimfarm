from typing import Optional


class Operation:
    """Base class for all operations

    Attributes:
        success (:obj:`bool`, optional): task is successful or not
        error_domain (optional): a code to identify which module produced the error
        error_code (optional): a code to identify the error if error occurred
        error_message (:obj:`str`, optional): a message to describe the error if error occurred
        std_out (:obj:`bytes`, optional): std_out
        std_err (:obj:`bytes`, optional): std_err
    """

    name: str = 'Operation Base Class'

    def __init__(self):
        self.success: Optional[bool] = None

        self.error_domain: Optional[str] = None
        self.error_code = None
        self.error_message: Optional[str] = None

        self.std_out: Optional[bytes] = None
        self.std_err: Optional[bytes] = None

    @property
    def result(self) -> {}:
        result = {'success': self.success, 'name': self.name}

        if self.error_domain is not None: result['error_domain'] = self.error_domain
        if self.error_code is not None: result['error_code'] = self.error_code
        if self.error_message is not None: result['error_message'] = self.error_message

        if self.std_out is not None: result['std_out'] = self.std_out
        if self.std_err is not None: result['std_err'] = self.std_err

        return result

    def execute(self):
        pass
