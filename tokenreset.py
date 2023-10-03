from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(uname,seconds):
    s=Serializer('bhargavi#2002',seconds)
    return s.dumps({'user':uname}).decode('utf-8')
