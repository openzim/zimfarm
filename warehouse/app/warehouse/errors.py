class MissingEnvironmentalVariable(Exception):
    def __init__(self, variable_name: str):
        self.variable_name = variable_name

    def __str__(self):
        return "Missing Environmental Variable {}".format(self.variable_name)
