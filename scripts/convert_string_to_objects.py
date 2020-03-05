import ast
import json

with open("data/tools.json"):
    tools = json.loads(o.read())

for t in tools:
    meta = t.pop("meta")
    t["meta"] = {}
    for k,v in meta.items():
        if k == "Chemical_List":
            if v == "":
                new_v = []
            else:
                new_v = ast.literal_eval(v)
            t["meta"][k.replace(" ","_")] = new_v
        elif k == "KeywordList":
            if v == "[]":
                new_v = []
            else:
                new_v = ast.literal_eval(v.replace("‚",","))[0]
            t["meta"][k.replace(" ","_")] = new_v
        elif not v == "":
            t["meta"][k.replace(" ","_")] = v

with open("data/tools.json", "w") as o:
    o.write(json.dumps(tools))  