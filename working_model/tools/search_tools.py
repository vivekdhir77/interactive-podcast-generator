
from langchain.tools import tool
import json
import requests
import os

class Search_tools:
    @tool("Search for knowledge")
    def search_serper(query):
        """useful to search internet about a given topic and return relevant results"""
        top_k_results = 4
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': os.getenv("SERPER_API_KEY"),
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        if "organic" not in response.json():
            return ""
        else:
            results = response.json()["organic"]
            string = []
            for result in results[:top_k_results]:
                try:
                    string.append('\n'.join([
                    f"Title: {result['title']}", f"Link: {result['link']}",
                    f"'Snippet: {result['snippet']}", "\n-------------------"]))
                except KeyError:
                    next
        return '\n'. join(string)