def empty_cleaner(obj):
    if type(obj) == str:
        obj = obj.strip()
        if obj == "":
            return None
        else:
            return obj
    elif type(obj) == list:
        new_list = []
        for i in obj:
            v = empty_cleaner(i)
            if v:
                new_list.append(v)
        if len(new_list) > 0:
            return new_list
        else:
            return None
    elif type(obj) == dict:
        new_dict = {}
        for k,v in obj.items():
            val = empty_cleaner(v)
            if val:
                new_dict[k] = val
        if len(new_dict) > 0:
            return new_dict
        else:
            return None
    else:
        return obj