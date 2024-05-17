from Databases.Remote.Firebase.Firebase import Firebase


class RemoteStorage:

    @staticmethod
    def get_storage():
        return Firebase.get_instance()
