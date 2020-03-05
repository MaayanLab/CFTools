from ingestion import create_schema, post_data
import requests
import ast
from requests.auth import HTTPBasicAuth
import os
import json

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

APIurl = "http://nih-cfde-tools.org/metadata-api/%s/%s"

auth = HTTPBasicAuth(username, password)
credential = base64.b64encode('{username}:{password}'.format(
    username=username, password=password
  ).encode()).decode()

# schemas
with open("schemas/landing.json") as o:
    landing = json.loads(o.read())

landing = create_schema(landing[0], "/dcic/signature-commons-schema/v5/meta/schema/landing-ui.json")
post_data([landing], "schemas",
                     PATCHurl=APIurl, credential=credential)

with open("schemas/ui-schemas/resource.json") as o:
    resource = json.loads(o.read(),
                     PATCHurl=APIurl, credential=credential)

resource = create_schema(resource, "/dcic/signature-commons-schema/v5/meta/schema/ui-schema.json")
post_data([resource], "schemas",
                     PATCHurl=APIurl, credential=credential)

with open("schemas/ui-schemas/library.json") as o:
    library = json.loads(o.read())

library = create_schema(library, "/dcic/signature-commons-schema/v5/meta/schema/ui-schema.json")
post_data([library], "schemas",
                     PATCHurl=APIurl, credential=credential)

with open("schemas/ui-schemas/signature.json") as o:
    signature = json.loads(o.read())

signature = create_schema(signature, "/dcic/signature-commons-schema/v5/meta/schema/ui-schema.json")
post_data([signature], "schemas",
                     PATCHurl=APIurl, credential=credential)

# Programs
with open("data/programs.json") as o:
    programs = json.loads(o.read())
    post_data(programs, "resources",
                     PATCHurl=APIurl, credential=credential)


# Projects
with open("data/projects.json") as o:
    projects = json.loads(o.read())
    post_data(projects, "libraries",
                     PATCHurl=APIurl, credential=credential)

# Tools
with open("data/tools.json") as o:
    tools = json.loads(o.read())
    post_data(tools, "signatures",
                     PATCHurl=APIurl, credential=credential)

res = requests.get(APIurl%("optimize","refresh"), auth=auth)
print(res.ok)
res = requests.get(APIurl%("summary","refresh"), auth=auth)
print(res.ok)