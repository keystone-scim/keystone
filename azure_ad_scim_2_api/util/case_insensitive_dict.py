from collections import abc


class CaseInsensitiveDict(dict):
    proxy = {}

    def __init__(self, data):
        super().__init__()
        self.proxy = dict((k.lower(), k) for k in data)
        for k in data:
            self[k] = data[k]

    def __contains__(self, k):
        return k.lower() in self.proxy

    def __delitem__(self, k):
        key = self.proxy[k.lower()]
        super(CaseInsensitiveDict, self).__delitem__(key)
        del self.proxy[k.lower()]

    def __getitem__(self, k):
        key = self.proxy[k.lower()]
        return super(CaseInsensitiveDict, self).__getitem__(key)

    def get(self, k, default=None):
        return self[k] if k in self else default

    def __setitem__(self, k, v):
        super(CaseInsensitiveDict, self).__setitem__(k, v)
        self.proxy[k.lower()] = k

    @staticmethod
    async def build_deep(d):
        ci_dict = CaseInsensitiveDict(d)
        for k in ci_dict:
            if type(d[k]) is dict:
                ci_dict[k] = await CaseInsensitiveDict.build_deep(ci_dict[k])
        return ci_dict
