ioregister = CoramIoRegister(idx=0, datawidth=32)
register = CoramRegister(idx=0, datawidth=32)
while True:
    val = register.read()
    ioregister.write(val)
