import random

from elasticsearch import Elasticsearch


class SearchEngine:

    def __init__(self):
        self.api_key = "--"

        self.client = Elasticsearch(
            "--",
            api_key=self.api_key
        )

    def set_data(self, documents):
        format_docs = []
        for doc in documents:
            format_docs.append(
                {"index": {"_index": "search-champions", "_id": str(random.randint(10000000, 99999999))}})
            format_docs.append(doc)
        self.client.bulk(operations=format_docs, pipeline="ent-search-generic-ingestion")

    def search(self, query):
        result = self.client.search(index="search-champions", q=query)
        return result

    # Function to delete a document by id
    def delete_by_id(self, document_id):
        response = self.client.delete(index="search-champions", id=document_id)
        return response

    # Function to delete all documents in an index
    def wipe_index(self):
        response = self.client.indices.delete(index="search-champions", ignore=[400, 404])
        return response
