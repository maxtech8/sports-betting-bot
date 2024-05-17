from Databases.Remote.DatabaseSingelton import Database
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from Configurations import ConfigSingleton


# Firebase implementation
class Firebase(Database):
    def __init__(self):
        # super()._instance = self
        super().__init__()
        self.db = self.init_db(
            ConfigSingleton.PRJ_DIR_PATH + self.prjConfig["Database"]["Firebase"]["Keys_File_Name"])

    def init_db(self, *args):
        firebase_cred = credentials.Certificate(args[0])
        firebase_admin.initialize_app(firebase_cred)
        db = firestore.client()
        return db

    async def close_db(self):
        pass

    async def update(self, *args):
        arguments_dict = args[0]
        path = arguments_dict["path"]
        data = arguments_dict["data"]
        try:
            self.db.document(path).update(data)
        except Exception as e:
            self.logger.error(
                f"Failed to update in Firebase: path: {path}, data: {data}, Exception: {e}")

    async def post(self, *args):
        arguments_dict = args[0]
        path = arguments_dict["path"]
        data = arguments_dict["data"]

        try:
            self.db.document(path).set(data)
            return True
        except Exception as e:
            print(e)
            self.logger.error(
                f"Firebase Failed to backup: path: {path}, data: {data}, Exception: {e}")

    async def get(self, *args):
        arguments_dict = args[0]
        path = arguments_dict["path"]
        if "isCollection" in arguments_dict and arguments_dict["isCollection"]:
            col = self.db.collection(path)
            res = {}
            for doc in col.stream():
                res[doc.id] = doc.to_dict()
            return res
        else:
            doc = self.db.document(path).get()
            if not doc.exists:
                self.logger.error(
                    f"Firebase get failed. Failed to get: path: {path}")
            return doc.to_dict()


    async def delete(self, *args):
        arguments_dict = args[0]
        path = arguments_dict["path"]
        try:
            self.db.document(path).delete()
        except Exception as e:
            self.logger.error(
                f"Firebase delete failed. Failed to delete: path: {path}, Exception: {e}")

# s = Firebase.get_instance()
# s.update({"path": "t/event_id_example_1", "data": {"Participants": [{"user_id": "123"}, {"user_id": "123"}]}})
# s.post({"collection_name": "t", "data": {"Yuval": 5, "Dodo": 1}})
# s.post({"collection_name": "t", "data": {"Yuval": 5, "Dodo": 1}})
# x = s.get({"collection_name": "t", "document_name": "OyGFSw4SiSNiSLdaNLzT"})
# print(x)
