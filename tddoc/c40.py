__doc__ = "C40 codec"

# Just arbitrarily map FNC1 to u0080
fnc1 = '\x80'

class Codec:
    def __init__(self, sets):
        self.sets = sets
        self.reverse = self._reverse_gen(sets)

    @staticmethod
    def _reverse_gen(sets):
        r = {}
        for i, set in enumerate(sets):
            for code, char in set.items():
                r[char] = i, code
        return r

    @staticmethod
    def stream_extract(cw):
        cw2 = []
        for off in range(0, len(cw), 2):
            c = int.from_bytes(cw[off : off + 2], "big")
            if c == 254:
                break
            cw2.append(c)
        return cw2

    @staticmethod
    def unpack(s):
        c = []
        for v in s:
            c1 = (v-1) // 1600
            c2 = ((v-1) // 40) % 40
            c3 = (v-1) % 40

            c.append(c1)
            c.append(c2)
            c.append(c3)
        return c

    @staticmethod
    def ascii_decode(cs, sets):
        lock = False
        s = 0

        ret = ''
        for c in cs:
            if s == 0 and c <= 2:
                s = c + 1
                continue
            if s == 2 and c == 30:
                lock = True
                s = 0
            try:
                ret += sets[s][c]
            except:
                raise ValueError("Bad encoding")
            if not lock:
                s = 0

        return ret

    def parse(self, c40):
        cw = self.stream_extract(c40)
        cs = self.unpack(cw)
        return self.ascii_decode(cs, self.sets)

    @staticmethod
    def text_encode(text, mapping):
        s = 0
        ret = []
        for c in text:
            set, code = mapping[c]
            if s != set:
                if s == 0:
                    ret.append(set-1)
                else:
                    raise ValueError("Cannot encode", set, c)
            ret.append(code)
        return ret

    @staticmethod
    def pack(cs):
        if len(cs) % 3 == 2:
            cs = cs + [0]
        elif len(cs) % 3 == 1:
            cs = cs + [1, 30]

        ret = []
        for off in range(0, len(cs), 3):
            v = cs[off] * 1600 + cs[off + 1] * 40 + cs[off + 2] + 1
            ret.append(v)
        return ret

    @staticmethod
    def stream_format(cw):
        return b''.join(x.to_bytes(2, "big") for x in cw)

    def format(self, text):
        cs = self.text_encode(text, self.reverse)
        cw = self.pack(cs)
        return self.stream_format(cw)

set0_c40 = {(i+3):v for (i, v) in enumerate(" 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
set0_text = {k:v.lower() for (k, v) in set0_c40.items()}
set1 = {i:chr(i) for i in range(32)}
set2 = {i:v for (i, v) in enumerate("!\"#$%&'()*+,-./:;<=>?@[\\]^_"+fnc1)}
set3_c40 = {i:v for (i, v) in enumerate("`abcdefghijklmnopqrstuvwxyz{|}~\x7f")}
set3_text = {k:v.upper() for (k, v) in set3_c40.items()}

# Define both C40 and Text mode, even if this project only uses C40.
c40 = Codec([set0_c40, set1, set2, set3_c40])
text = Codec([set0_text, set1, set2, set3_text])
