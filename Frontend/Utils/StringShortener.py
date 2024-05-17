class StringShortener:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StringShortener, cls).__new__(cls)
            # Put any initialization here.
            cls._instance.dictionary = {}
            cls._instance.counter = 0
        return cls._instance

    def shorten(self, original_string):
        # Generate a unique key for the original string
        key = f"{self.counter}"
        self.dictionary[key] = original_string
        self.counter += 1
        return key

    def retrieve_original(self, shortened_string):
        return self.dictionary.get(shortened_string, None)