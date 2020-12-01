class ModelProcessResult:
    def __init__(self, predictions, images):
        self.__predictions = predictions
        self.__images = images

    @property
    def predictions(self):
      return self.__predictions

    @property
    def images(self):
        return self.__images
