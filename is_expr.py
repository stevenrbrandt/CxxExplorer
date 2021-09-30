import re

def is_expr(s):
    pat = r'''(?x)
    (
    //.*| # one line comments
    /\*[\d\D]*?\*/| # long comments
    (\w+(?:::\w+)*(?:\.\w+(?:::\w+)*)*)| # identifier
    \s+| # spaces
    (<<|>>|[-+=*%/\[(]) # operator
    )'''
    res = []
    while len(res) < 2:
        g = re.match(pat, s)
        if g:
            if g.group(2) is not None and g.group(2) not in ["is_same","decltype"]:
                res += ["S"]
            elif g.group(3) is not None:
                res += ["O"]
            s = s[g.end():]
        else:
            break
    if len(res) == 2 and res[0] == "S" and res[1] == "O":
        return True
    else:
        return False

if __name__ == "__main__":
    for v in [("a++;",True),
              ("cout << \"Hello\" << endl;",True),
              ("struct foo {};",False),
              ("int fib(int n);",False),
              ("template<typename T> fib(T t);",False),
              ("std::cout <<",True),
              ("hpx::cout <<",True),
              ("int a;",False),
              ("std::vector<int> v;",False),
              ("v.clear();",True),
              ("cin >>",True),
              ("std::cin >>",True)]:
        print(v)
        s,r = v
        assert is_expr(s) == r
