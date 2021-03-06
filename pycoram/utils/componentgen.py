import xml.dom.minidom
import codecs
import datetime

PORTLIST = ('AWID', 'AWADDR', 'AWLEN', 'AWSIZE', 'AWBURST', 'AWLOCK',
            'AWCACHE', 'AWPROT', 'AWQOS', 'AWUSER', 'AWVALID', 'AWREADY',
            'WDATA', 'WSTRB', 'WLAST', 'WUSER', 'WVALID', 'WREADY', 
            'BID', 'BRESP', 'BUSER', 'BVALID', 'BREADY', 
            'ARID', 'ARADDR', 'ARLEN', 'ARSIZE', 'ARBURST', 'ARLOCK',
            'ARCACHE', 'ARPROT', 'ARQOS', 'ARUSER', 'ARVALID', 'ARREADY', 
            'RID', 'RDATA', 'RRESP', 'RLAST', 'RUSER', 'RVALID', 'RREADY' )

PORTLITELIST = ('AWADDR', 'AWPROT', 'AWVALID', 'AWREADY',
                'WDATA', 'WSTRB', 'WVALID', 'WREADY', 
                'BRESP', 'BVALID', 'BREADY', 
                'ARADDR', 'ARPROT', 'ARVALID', 'ARREADY', 
                'RDATA', 'RRESP', 'RVALID', 'RREADY' )

#-------------------------------------------------------------------------------
class ComponentGen(object):
    def __init__(self):
        self.impl = None
        self.doc = None
        self.top = None
        self.userlogic_name = None
        self.threads = None
        self.lite = False
        self.ext_addrwidth = 32
        self.ext_burstlength = 256
        self.ext_ports = ()
        self.ext_params = ()

    #---------------------------------------------------------------------------
    def generate(self, userlogic_name, threads,
                 lite=False, ext_addrwidth=32, ext_burstlength=256, ext_ports=(), ext_params=()):
        self.userlogic_name = userlogic_name
        self.threads = threads
        self.lite = lite
        self.ext_addrwidth = ext_addrwidth
        self.ext_burstlength = ext_burstlength
        self.ext_ports = ext_ports
        self.ext_params = ext_params

        self.init()
        
        self.top.appendChild(self.mkVendor())
        self.top.appendChild(self.mkLibrary())
        self.top.appendChild(self.mkName('pycoram_' + self.userlogic_name.lower()))
        self.top.appendChild(self.mkVersion())
        self.top.appendChild(self.mkBusInterfaces())
        r = self.mkAddressSpaces()
        if r: self.top.appendChild(r)
        r = self.mkMemoryMaps()
        if r: self.top.appendChild(r)
        self.top.appendChild(self.mkModel())
        self.top.appendChild(self.mkChoices())
        self.top.appendChild(self.mkFileSets())
        self.top.appendChild(self.mkDescription())
        self.top.appendChild(self.mkParameters())
        self.top.appendChild(self.mkVendorExtensions())

        return self.doc.toprettyxml(indent='  ')

    #---------------------------------------------------------------------------
    def setAttribute(self, obj, name, text):
        attrobj = self.doc.createAttribute(name)
        attrobj.value = str(text)
        obj.setAttributeNode(attrobj)
    
    def setText(self, obj, text):
        textobj = self.doc.createTextNode(str(text))
        obj.appendChild(textobj)

    #---------------------------------------------------------------------------
    def init(self):
        self.impl = xml.dom.minidom.getDOMImplementation()
        self.doc = self.impl.createDocument('spirit', 'spirit:component', None)
        self.top = self.doc.documentElement
        
        self.setAttribute(self.top, 'xmlns:xilinx', "http://www.xilinx.com")
        self.setAttribute(self.top, 'xmlns:spirit',
                          "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009")
        self.setAttribute(self.top, 'xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")

    #---------------------------------------------------------------------------
    def mkVendor(self):
        vendor = self.doc.createElement('spirit:vendor')
        self.setText(vendor, 'PyCoRAM')
        return vendor

    def mkLibrary(self):
        library = self.doc.createElement('spirit:library')
        self.setText(library, 'user')
        return library

    def mkVersion(self):
        version = self.doc.createElement('spirit:version')
        self.setText(version, str(1.0))
        return version

    def mkName(self, v):
        name = self.doc.createElement('spirit:name')
        self.setText(name, v)
        return name

    #---------------------------------------------------------------------------
    def mkTextNode(self, n, v):
        name = self.doc.createElement(n)
        self.setText(name, v)
        return name

    #---------------------------------------------------------------------------
    def mkBusInterfaces(self):
        bus = self.doc.createElement('spirit:busInterfaces')
        for thread in self.threads:
            for memory in thread.memories:
                bus.appendChild(self.mkBusInterface(thread, memory))
            for instream in thread.instreams:
                bus.appendChild(self.mkBusInterface(thread, instream))
            for outstream in thread.outstreams:
                bus.appendChild(self.mkBusInterface(thread, outstream))
            for iochannel in thread.iochannels:
                bus.appendChild(self.mkBusInterface(thread, iochannel, master=False, lite=self.lite))
            for ioregister in thread.ioregisters:
                bus.appendChild(self.mkBusInterface(thread, ioregister, master=False, lite=self.lite))
        for thread in self.threads:
            for memory in thread.memories:
                bus.appendChild(self.mkBusInterfaceReset(thread, memory))
                bus.appendChild(self.mkBusInterfaceClock(thread, memory))
            for instream in thread.instreams:
                bus.appendChild(self.mkBusInterfaceReset(thread, instream))
                bus.appendChild(self.mkBusInterfaceClock(thread, instream))
            for outstream in thread.outstreams:
                bus.appendChild(self.mkBusInterfaceReset(thread, outstream))
                bus.appendChild(self.mkBusInterfaceClock(thread, outstream))
            for iochannel in thread.iochannels:
                bus.appendChild(self.mkBusInterfaceReset(thread, iochannel))
                bus.appendChild(self.mkBusInterfaceClock(thread, iochannel))
            for ioregister in thread.ioregisters:
                bus.appendChild(self.mkBusInterfaceReset(thread, ioregister))
                bus.appendChild(self.mkBusInterfaceClock(thread, ioregister))
        return bus

    #---------------------------------------------------------------------------
    def mkBusInterface(self, thread, obj, master=True, lite=False):
        name = thread.name + '_' + obj.name + '_AXI'
        datawidth = obj.ext_datawidth
        interface = self.doc.createElement('spirit:busInterface')
        interface.appendChild(self.mkName(name))
        interface.appendChild(self.mkBusType())
        interface.appendChild(self.mkAbstractionType())
        if master:
            interface.appendChild(self.mkMaster(name))
        else:
            interface.appendChild(self.mkSlave(name))
        interface.appendChild(self.mkPortMaps(name, lite))
        interface.appendChild(self.mkBusParameters(name, datawidth, master))
        return interface

    def mkBusType(self):
        bustype = self.doc.createElement('spirit:busType')
        self.setAttribute(bustype, 'spirit:vendor', "xilinx.com")
        self.setAttribute(bustype, 'spirit:library', "interface")
        self.setAttribute(bustype, 'spirit:name', "aximm")
        self.setAttribute(bustype, 'spirit:version', "1.0")
        return bustype

    def mkAbstractionType(self):
        abstractiontype = self.doc.createElement('spirit:abstractionType')
        self.setAttribute(abstractiontype, 'spirit:vendor', "xilinx.com")
        self.setAttribute(abstractiontype, 'spirit:library', "interface")
        self.setAttribute(abstractiontype, 'spirit:name', "aximm_rtl")
        self.setAttribute(abstractiontype, 'spirit:version', "1.0")
        return abstractiontype

    def mkMaster(self, name):
        master = self.doc.createElement('spirit:master')
        addressspaceref = self.doc.createElement('spirit:addressSpaceRef')
        self.setAttribute(addressspaceref, 'spirit:addressSpaceRef', name)
        master.appendChild(addressspaceref)
        return master
    
    def mkSlave(self, name):
        slave = self.doc.createElement('spirit:slave')
        memorymapref = self.doc.createElement('spirit:memoryMapRef')
        self.setAttribute(memorymapref, 'spirit:memoryMapRef', name)
        slave.appendChild(memorymapref)
        return slave

    def mkPortMaps(self, name, lite=False):
        portmaps = self.doc.createElement('spirit:portMaps')
        if lite:
            for port in PORTLITELIST:
                portmaps.appendChild(self.mkPortMap(name, port))
        else:
            for port in PORTLIST:
                portmaps.appendChild(self.mkPortMap(name, port))
        return portmaps

    def mkPortMap(self, name, attr):
        portmap = self.doc.createElement('spirit:portMap')
        portmap.appendChild(self.mkLogicalPort(attr))
        portmap.appendChild(self.mkPhysicalPort(name, attr))
        return portmap

    def mkLogicalPort(self, attr):
        logicalport = self.doc.createElement('spirit:logicalPort')
        logicalport.appendChild(self.mkName(attr))
        return logicalport
    
    def mkPhysicalPort(self, name, attr):
        physicalport = self.doc.createElement('spirit:physicalPort')
        physicalport.appendChild(self.mkName(name + '_' + attr))
        return physicalport
    
    def mkBusParameters(self, name, datawidth, master=True):
        parameters = self.doc.createElement('spirit:parameters')
        parameters.appendChild(self.mkBusParameterDatawidth(name, datawidth))
        if master:
            parameters.appendChild(self.mkBusParameterNumReg(name, 4))
        parameters.appendChild(self.mkBusParameterBurst(name, 0))
        return parameters

    def mkBusParameterDatawidth(self, name, datawidth):
        parameter = self.doc.createElement('spirit:parameter')
        parameter.appendChild(self.mkName('WIZ.DATA_WIDTH'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:format', "long")
        self.setAttribute(value, 'spirit:id', "BUSIFPARAM_VALUE." +
                          name + ".WIZ.DATA_WIDTH")
        self.setAttribute(value, 'spirit:choiceRef', "choices_0")
        self.setText(value, datawidth)
        parameter.appendChild(value)
        return parameter

    def mkBusParameterNumReg(self, name, num_reg):
        parameter = self.doc.createElement('spirit:parameter')
        parameter.appendChild(self.mkName('WIZ.NUM_REG'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:format', "long")
        self.setAttribute(value, 'spirit:id', "BUSIFPARAM_VALUE." +
                          name + ".WIZ.NUM_REG")
        self.setAttribute(value, 'spirit:minimum', "4")
        self.setAttribute(value, 'spirit:maximum', "512")
        self.setAttribute(value, 'spirit:rangeType', "long")
        self.setText(value, num_reg)
        parameter.appendChild(value)
        return parameter

    def mkBusParameterBurst(self, name, num):
        parameter = self.doc.createElement('spirit:parameter')
        parameter.appendChild(self.mkName('SUPPORTS_NARROW_BURST'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:format', "long")
        self.setAttribute(value, 'spirit:id', "BUSIFPARAM_VALUE." +
                          name + ".SUPPORTS_NARROW_BURST")
        self.setAttribute(value, 'spirit:choiceRef', "choices_1")
        self.setText(value, num)
        parameter.appendChild(value)
        return parameter

    #---------------------------------------------------------------------------
    def mkBusInterfaceReset(self, thread, obj):
        name = thread.name + '_' + obj.name + '_AXI'
        datawidth = obj.ext_datawidth
        interface = self.doc.createElement('spirit:busInterface')
        interface.appendChild(self.mkName(name + '_RST'))
        interface.appendChild(self.mkBusTypeReset())
        interface.appendChild(self.mkAbstractionTypeReset())
        interface.appendChild(self.mkSlaveReset())
        interface.appendChild(self.mkPortMapsReset(name))
        interface.appendChild(self.mkBusParametersReset(name))
        return interface

    def mkBusTypeReset(self):
        bustype = self.doc.createElement('spirit:busType')
        self.setAttribute(bustype, 'spirit:vendor', "xilinx.com")
        self.setAttribute(bustype, 'spirit:library', "signal")
        self.setAttribute(bustype, 'spirit:name', "reset")
        self.setAttribute(bustype, 'spirit:version', "1.0")
        return bustype

    def mkAbstractionTypeReset(self):
        abstractiontype = self.doc.createElement('spirit:abstractionType')
        self.setAttribute(abstractiontype, 'spirit:vendor', "xilinx.com")
        self.setAttribute(abstractiontype, 'spirit:library', "signal")
        self.setAttribute(abstractiontype, 'spirit:name', "reset_rtl")
        self.setAttribute(abstractiontype, 'spirit:version', "1.0")
        return abstractiontype

    def mkSlaveReset(self):
        slave = self.doc.createElement('spirit:slave')
        return slave

    def mkPortMapsReset(self, name):
        portmaps = self.doc.createElement('spirit:portMaps')
        portmaps.appendChild(self.mkPortMapReset(name))
        return portmaps

    def mkPortMapReset(self, name):
        portmap = self.doc.createElement('spirit:portMap')
        portmap.appendChild(self.mkLogicalPort('RST'))
        portmap.appendChild(self.mkPhysicalPortReset(name))
        return portmap

    def mkPhysicalPortReset(self, name):
        physicalport = self.doc.createElement('spirit:physicalPort')
        physicalport.appendChild(self.mkName(name + '_' + 'ARESETN'))
        return physicalport
    
    def mkBusParametersReset(self, name):
        parameters = self.doc.createElement('spirit:parameters')
        parameters.appendChild(self.mkBusParameterPolarity(name))
        return parameters

    def mkBusParameterPolarity(self, name):
        parameter = self.doc.createElement('spirit:parameter')
        parameter.appendChild(self.mkName('POLARITY'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:id', "BUSIFPARAM_VALUE." +
                          name + ".POLARITY")
        self.setText(value, 'ACTIVE_LOW')
        parameter.appendChild(value)
        return parameter

    #---------------------------------------------------------------------------
    def mkBusInterfaceClock(self, thread, obj):
        name = thread.name + '_' + obj.name + '_AXI'
        datawidth = obj.ext_datawidth
        interface = self.doc.createElement('spirit:busInterface')
        interface.appendChild(self.mkName(name + '_CLK'))
        interface.appendChild(self.mkBusTypeClock())
        interface.appendChild(self.mkAbstractionTypeClock())
        interface.appendChild(self.mkSlaveClock())
        interface.appendChild(self.mkPortMapsClock(name))
        interface.appendChild(self.mkBusParametersClock(name))
        return interface

    def mkBusTypeClock(self):
        bustype = self.doc.createElement('spirit:busType')
        self.setAttribute(bustype, 'spirit:vendor', "xilinx.com")
        self.setAttribute(bustype, 'spirit:library', "signal")
        self.setAttribute(bustype, 'spirit:name', "clock")
        self.setAttribute(bustype, 'spirit:version', "1.0")
        return bustype

    def mkAbstractionTypeClock(self):
        abstractiontype = self.doc.createElement('spirit:abstractionType')
        self.setAttribute(abstractiontype, 'spirit:vendor', "xilinx.com")
        self.setAttribute(abstractiontype, 'spirit:library', "signal")
        self.setAttribute(abstractiontype, 'spirit:name', "clock_rtl")
        self.setAttribute(abstractiontype, 'spirit:version', "1.0")
        return abstractiontype

    def mkSlaveClock(self):
        slave = self.doc.createElement('spirit:slave')
        return slave

    def mkPortMapsClock(self, name):
        portmaps = self.doc.createElement('spirit:portMaps')
        portmaps.appendChild(self.mkPortMapClock(name))
        return portmaps

    def mkPortMapClock(self, name):
        portmap = self.doc.createElement('spirit:portMap')
        portmap.appendChild(self.mkLogicalPort('CLK'))
        portmap.appendChild(self.mkPhysicalPortClock(name))
        return portmap

    def mkPhysicalPortClock(self, name):
        physicalport = self.doc.createElement('spirit:physicalPort')
        physicalport.appendChild(self.mkName(name + '_' + 'ACLK'))
        return physicalport
    
    def mkBusParametersClock(self, name):
        parameters = self.doc.createElement('spirit:parameters')
        parameters.appendChild(self.mkBusParameterAssocBusIf(name))
        parameters.appendChild(self.mkBusParameterAssocReset(name))
        return parameters

    def mkBusParameterAssocBusIf(self, name):
        parameter = self.doc.createElement('spirit:parameter')
        parameter.appendChild(self.mkName('ASSOCIATED_BUSIF'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:id', "BUSIFPARAM_VALUE." +
                          name + ".ASSOCIATED_BUSIF")
        self.setText(value, name)
        parameter.appendChild(value)
        return parameter

    def mkBusParameterAssocReset(self, name):
        parameter = self.doc.createElement('spirit:parameter')
        parameter.appendChild(self.mkName('ASSOCIATED_RESET'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:id', "BUSIFPARAM_VALUE." +
                          name + ".ASSOCIATED_RESET")
        self.setText(value, name + '_ARESETN')
        parameter.appendChild(value)
        return parameter

    #---------------------------------------------------------------------------
    def mkAddressSpaces(self):
        isempty = True
        spaces = self.doc.createElement('spirit:addressSpaces')
        for thread in self.threads:
            for memory in thread.memories:
                spaces.appendChild(self.mkAddressSpace(thread, memory))
                isempty = False
            for instream in thread.instreams:
                spaces.appendChild(self.mkAddressSpace(thread, instream))
                isempty = False
            for outstream in thread.outstreams:
                spaces.appendChild(self.mkAddressSpace(thread, outstream))
                isempty = False
        if isempty: return None
        return spaces

    def mkAddressSpace(self, thread, obj):
        name = thread.name + '_' + obj.name + '_AXI'
        space = self.doc.createElement('spirit:addressSpace')
        space.appendChild(self.mkName(name))
        range = self.doc.createElement('spirit:range')
        self.setAttribute(range, 'spirit:format', "long")
        self.setAttribute(range, 'spirit:resolve', "dependent")
        self.setAttribute(range, 'spirit:dependency',
                          ("pow(2,(spirit:decode(id('MODELPARAM_VALUE.C_" +
                           name + "_ADDR_WIDTH')) - 1) + 1)"))
        self.setAttribute(range, 'spirit:minimum', "0")
        self.setAttribute(range, 'spirit:maximum', "4294967296")
        self.setText(range, 4294967296)
        space.appendChild(range)
        width = self.doc.createElement('spirit:width')
        self.setAttribute(width, 'spirit:format', "long")
        self.setAttribute(width, 'spirit:resolve', "dependent")
        self.setAttribute(width, 'spirit:dependency',
                          ("(spirit:decode(id('MODELPARAM_VALUE.C_" +
                           name + "_DATA_WIDTH')) - 1) + 1"))
        self.setText(width, self.ext_addrwidth)
        space.appendChild(width)
        return space

    #---------------------------------------------------------------------------
    def mkMemoryMaps(self):
        isempty = True
        maps = self.doc.createElement('spirit:memoryMaps')
        for thread in self.threads:
            for iochannel in thread.iochannels:
                maps.appendChild(self.mkMemoryMap(thread, iochannel))
                isempty = False
            for ioregister in thread.ioregisters:
                maps.appendChild(self.mkMemoryMap(thread, ioregister))
                isempty = False
        if isempty: return None
        return maps
    
    def mkMemoryMap(self, thread, obj):
        name = thread.name + '_' + obj.name + '_AXI'
        map = self.doc.createElement('spirit:memoryMap')
        map.appendChild(self.mkName(name))
        addressblock = self.doc.createElement('spirit:addressBlock')
        addressblock.appendChild(self.mkName(name + '_reg'))
        baseaddr = self.doc.createElement('spirit:baseAddress')
        self.setAttribute(baseaddr, 'spirit:format', "long")
        self.setAttribute(baseaddr, 'spirit:resolve', "user")
        self.setText(baseaddr, 0)
        addressblock.appendChild(baseaddr)
        range = self.doc.createElement('spirit:range')
        self.setAttribute(range, 'spirit:format', "long")
        self.setText(range, 4096)
        addressblock.appendChild(range)
        width = self.doc.createElement('spirit:width')
        self.setAttribute(width, 'spirit:format', "long")
        self.setText(width, obj.ext_datawidth)
        addressblock.appendChild(width)
        usage = self.doc.createElement('spirit:usage')
        self.setText(usage, 'register')
        addressblock.appendChild(usage)
        addressblock.appendChild(self.mkMemoryMapParameters(name))
        map.appendChild(addressblock)
        return map

    def mkMemoryMapParameters(self, name):
        parameters = self.doc.createElement('spirit:parameters')
        parameters.appendChild(self.mkMemoryMapParameterBase(name))
        parameters.appendChild(self.mkMemoryMapParameterHigh(name))
        return parameters
    
    def mkMemoryMapParameterBase(self, name):
        base = self.doc.createElement('spirit:parameter')
        base.appendChild(self.mkName('OFFSET_BASE_PARAM'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:id',
                          "ADDRBLOCKPARAM_VALUE." + name + "_REG.OFFSET_BASE_PARAM")
        self.setAttribute(value, 'spirit:dependency',
                          "ADDRBLOCKPARAM_VALUE." + name + "_reg.OFFSET_BASE_PARAM")
        self.setText(value, 'C_' + name + '_BASEADDR')
        base.appendChild(value)
        return base

    def mkMemoryMapParameterHigh(self, name):
        high = self.doc.createElement('spirit:parameter')
        high.appendChild(self.mkName('OFFSET_HIGH_PARAM'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:id',
                          "ADDRBLOCKPARAM_VALUE." + name + "_REG.OFFSET_HIGH_PARAM")
        self.setAttribute(value, 'spirit:dependency',
                          "ADDRBLOCKPARAM_VALUE." + name + "_reg.OFFSET_HIGH_PARAM")
        self.setText(value, 'C_' + name + '_HIGHADDR')
        high.appendChild(value)
        return high

    #---------------------------------------------------------------------------
    def mkModel(self):
        model = self.doc.createElement('spirit:model')
        model.appendChild(self.mkViews())
        model.appendChild(self.mkPorts())
        model.appendChild(self.mkModelParameters())
        return model
    
    #---------------------------------------------------------------------------
    def mkViews(self):
        views = self.doc.createElement('spirit:views')
        views.appendChild(self.mkView('xilinx_verilogsynthesis',
                                      'Verilog Synthesis',
                                      'verilogSource:vivado.xilinx.com:synthesis',
                                      'verilog',
                                      'pycoram_' + self.userlogic_name.lower(),
                                      'xilinx_verilogsynthesis_view_fileset'))
        views.appendChild(self.mkView('xilinx_verilogbehavioralsimulation',
                                      'Verilog Simulation',
                                      'verilogSource:vivado.xilinx.com:simulation',
                                      'verilog',
                                      'pycoram_' + self.userlogic_name.lower(),
                                      'xilinx_verilogbehavioralsimulation_view_fileset'))
        views.appendChild(self.mkView('xilinx_synthesisconstraints',
                                      'Synthesis Constraints',
                                      ':vivado.xilinx.com:synthesis.constraints',
                                      None,
                                      None,
                                      'xilinx_synthesisconstraints_view_fileset'))
#        views.appendChild(self.mkView('xilinx_softwaredriver'
#                                      'Software Driver',
#                                      'Verilog Simulation',
#                                      ':vivado.xilinx.com:sw.driver',
#                                      None,
#                                      None,
#                                      'xilinx_softwaredriver_view_fileset'))
        views.appendChild(self.mkView('xilinx_xpgui',
                                      'UI Layout',
                                      ':vivado.xilinx.com:xgui.ui',
                                      None,
                                      None,
                                      'xilinx_xpgui_view_fileset'))
        views.appendChild(self.mkView('bd_tcl',
                                      'Block Diagram',
                                      ':vivado.xilinx.com:block.diagram',
                                      None,
                                      None,
                                      'bd_tcl_view_fileset'))
        return views
                         
    def mkView(self, name, displayname, envidentifier, language, modelname, localname):
        view = self.doc.createElement('spirit:view')
        view.appendChild(self.mkName(name))
        view.appendChild(self.mkTextNode('spirit:displayName', displayname))
        view.appendChild(self.mkTextNode('spirit:envIdentifier', envidentifier))
        
        if language is not None:
            view.appendChild(self.mkTextNode('spirit:language', language))

        if modelname is not None:
            view.appendChild(self.mkTextNode('spirit:modelName', modelname))
        
        filesetref = self.doc.createElement('spirit:fileSetRef')
        filesetref.appendChild(self.mkTextNode('spirit:localName', localname))
        view.appendChild(filesetref)
        
        return view
        
    #---------------------------------------------------------------------------
    def mkPorts(self):
        ports = self.doc.createElement('spirit:ports')
        ports.appendChild(self.mkPortEntry('UCLK', 'in',
                                           None, None, None, None))
        ports.appendChild(self.mkPortEntry('URESETN', 'in',
                                           None, None, None, None))
        for thread in self.threads:
            ports.appendChild(self.mkPortEntry(thread.name + '_CCLK', 'in',
                                               None, None, None, None))
            ports.appendChild(self.mkPortEntry(thread.name + '_CRESETN', 'in',
                                               None, None, None, None))
            for memory in thread.memories:
                for p in self.mkPortMaster(thread, memory): ports.appendChild(p)
            for instream in thread.instreams:
                for p in self.mkPortMaster(thread, instream): ports.appendChild(p)
            for outstream in thread.outstreams:
                for p in self.mkPortMaster(thread, outstream): ports.appendChild(p)
            for iochannel in thread.iochannels:
                for p in self.mkPortSlave(thread, iochannel, lite=self.lite):
                    ports.appendChild(p)
            for ioregister in thread.ioregisters:
                for p in self.mkPortSlave(thread, ioregister, lite=self.lite):
                    ports.appendChild(p)
        for portname, portdir, portlvalue in self.ext_ports:
            lvalue = portlvalue if portlvalue is not None else None
            rvalue = 0 if portlvalue is not None else None
            ports.appendChild(self.mkPortEntry(portname, portdir,
                                               None, lvalue, None, rvalue))
        return ports

    def mkPortMaster(self, thread, obj):
        base = thread.name + '_' + obj.name + '_AXI'
        datawidth = obj.ext_datawidth
        addrwidth = self.ext_addrwidth
        ret = []
        
        def mkStr(b, s):
            return "spirit:decode(id('MODELPARAM_VALUE.C_" + b + '_' + s + "'))"
        
        ret.append(self.mkPortEntry(base+'_AWID', 'out',
                                    '('+mkStr(base,'THREAD_ID_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'THREAD_ID_WIDTH')+' >0', 'true'))
        ret.append(self.mkPortEntry(base+'_AWADDR', 'out',
                                    '('+mkStr(base,'ADDR_WIDTH')+'-1)', addrwidth-1, None, 0))
        ret.append(self.mkPortEntry(base+'_AWLEN', 'out',
                                    None, 7, None, 0))
        ret.append(self.mkPortEntry(base+'_AWSIZE', 'out',
                                    None, 2, None, 0))
        ret.append(self.mkPortEntry(base+'_AWBURST', 'out',
                                    None, 1, None, 0))
        ret.append(self.mkPortEntry(base+'_AWLOCK', 'out',
                                    None, 1, None, 0))
        ret.append(self.mkPortEntry(base+'_AWCACHE', 'out',
                                    None, 3, None, 0))
        ret.append(self.mkPortEntry(base+'_AWPROT', 'out',
                                    None, 2, None, 0))
        ret.append(self.mkPortEntry(base+'_AWQOS', 'out',
                                    None, 3, None, 0))
        ret.append(self.mkPortEntry(base+'_AWUSER', 'out',
                                    '('+mkStr(base,'AWUSER_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'AWUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_AWVALID', 'out',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_AWREADY', 'in',
                                    None, None, None, None))
        
        ret.append(self.mkPortEntry(base+'_WDATA', 'out',
                                    '('+mkStr(base,'DATA_WIDTH')+'-1)', datawidth-1, None, 0))
        ret.append(self.mkPortEntry(base+'_WSTRB', 'out',
                                    '('+mkStr(base,'DATA_WIDTH')+'/8-1)', datawidth-1, None, 0))
        ret.append(self.mkPortEntry(base+'_WLAST', 'out',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_WUSER', 'out',
                                    '('+mkStr(base,'WUSER_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'WUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_WVALID', 'out',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_WREADY', 'in',
                                    None, None, None, None))
        
        ret.append(self.mkPortEntry(base+'_BID', 'in',
                                    '('+mkStr(base,'THREAD_ID_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'THREAD_ID_WIDTH')+' >0', 'true'))
        ret.append(self.mkPortEntry(base+'_BRESP', 'in',
                                    None, 1, None, 0))
        ret.append(self.mkPortEntry(base+'_BUSER', 'in',
                                    '('+mkStr(base,'BUSER_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'BUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_BVALID', 'in',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_BREADY', 'out',
                                    None, None, None, None))
        
        ret.append(self.mkPortEntry(base+'_ARID', 'out',
                                    '('+mkStr(base,'THREAD_ID_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'THREAD_ID_WIDTH')+' >0', 'true'))
        ret.append(self.mkPortEntry(base+'_ARADDR', 'out',
                                    '('+mkStr(base,'ADDR_WIDTH')+'-1)', addrwidth-1, None, 0))
        ret.append(self.mkPortEntry(base+'_ARLEN', 'out',
                                    None, 7, None, 0))
        ret.append(self.mkPortEntry(base+'_ARSIZE', 'out',
                                    None, 2, None, 0))
        ret.append(self.mkPortEntry(base+'_ARBURST', 'out',
                                    None, 1, None, 0))
        ret.append(self.mkPortEntry(base+'_ARLOCK', 'out',
                                    None, 1, None, 0))
        ret.append(self.mkPortEntry(base+'_ARCACHE', 'out',
                                    None, 3, None, 0))
        ret.append(self.mkPortEntry(base+'_ARPROT', 'out',
                                    None, 2, None, 0))
        ret.append(self.mkPortEntry(base+'_ARQOS', 'out',
                                    None, 3, None, 0))
        ret.append(self.mkPortEntry(base+'_ARUSER', 'out',
                                    '('+mkStr(base,'ARUSER_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'ARUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_ARVALID', 'out',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_ARREADY', 'in',
                                    None, None, None, None))
        
        ret.append(self.mkPortEntry(base+'_RID', 'in',
                                    '('+mkStr(base,'THREAD_ID_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'THREAD_ID_WIDTH')+' >0', 'true'))
        ret.append(self.mkPortEntry(base+'_RDATA', 'in',
                                    '('+mkStr(base,'DATA_WIDTH')+'-1)', datawidth-1, None, 0))
        ret.append(self.mkPortEntry(base+'_RRESP', 'in',
                                    None, 1, None, 0))
        ret.append(self.mkPortEntry(base+'_RLAST', 'in',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_RUSER', 'in',
                                    '('+mkStr(base,'RUSER_WIDTH')+'-1)', 0, None, 0,
                                    True, True, mkStr(base,'RUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_RVALID', 'in',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_RREADY', 'out',
                                    None, None, None, None))
        
        ret.append(self.mkPortEntry(base+'_ACLK', 'in',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_ARESETN', 'in',
                                    None, None, None, None))

        return ret
        
    def mkPortSlave(self, thread, obj, lite=False):
        base = thread.name + '_' + obj.name + '_AXI'
        datawidth = obj.ext_datawidth
        addrwidth = self.ext_addrwidth
        ret = []
        
        def mkStr(b, s):
            return "spirit:decode(id('MODELPARAM_VALUE.C_" + b + '_' + s + "'))"

        if not lite:
            ret.append(self.mkPortEntry(base+'_AWID', 'in',
                                        '('+mkStr(base,'THREAD_ID_WIDTH')+'-1)', 0, None, 0,
                                        True, True, mkStr(base,'THREAD_ID_WIDTH')+' >0', 'true'))
        ret.append(self.mkPortEntry(base+'_AWADDR', 'in',
                                    '('+mkStr(base,'ADDR_WIDTH')+'-1)', addrwidth-1, None, 0))
        if not lite:
            ret.append(self.mkPortEntry(base+'_AWLEN', 'in',
                                        None, 7, None, 0))
            ret.append(self.mkPortEntry(base+'_AWSIZE', 'in',
                                        None, 2, None, 0))
            ret.append(self.mkPortEntry(base+'_AWBURST', 'in',
                                        None, 1, None, 0))
            ret.append(self.mkPortEntry(base+'_AWLOCK', 'in',
                                        None, 1, None, 0))
            ret.append(self.mkPortEntry(base+'_AWCACHE', 'in',
                                        None, 3, None, 0))
        ret.append(self.mkPortEntry(base+'_AWPROT', 'in',
                                    None, 2, None, 0))
        if not lite:
            ret.append(self.mkPortEntry(base+'_AWQOS', 'in',
                                        None, 3, None, 0))
            ret.append(self.mkPortEntry(base+'_AWUSER', 'in',
                                        '('+mkStr(base,'AWUSER_WIDTH')+'-1)', 0, None, 0,
                                         True, True, mkStr(base,'AWUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_AWVALID', 'in',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_AWREADY', 'out',
                                    None, None, None, None))

        ret.append(self.mkPortEntry(base+'_WDATA', 'in',
                                    '('+mkStr(base,'DATA_WIDTH')+'-1)', datawidth-1, None, 0))
        ret.append(self.mkPortEntry(base+'_WSTRB', 'in',
                                    '('+mkStr(base,'DATA_WIDTH')+'/8-1)', datawidth-1, None, 0))
        if not lite:
            ret.append(self.mkPortEntry(base+'_WLAST', 'in',
                                        None, None, None, None))
            ret.append(self.mkPortEntry(base+'_WUSER', 'in',
                                        '('+mkStr(base,'WUSER_WIDTH')+'-1)', 0, None, 0,
                                        True, True, mkStr(base,'WUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_WVALID', 'in',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_WREADY', 'out',
                                    None, None, None, None))

        if not lite:
            ret.append(self.mkPortEntry(base+'_BID', 'out',
                                        '('+mkStr(base,'THREAD_ID_WIDTH')+'-1)', 0, None, 0,
                                        True, True, mkStr(base,'THREAD_ID_WIDTH')+' >0', 'true'))
        ret.append(self.mkPortEntry(base+'_BRESP', 'out',
                                    None, 1, None, 0))
        if not lite:
            ret.append(self.mkPortEntry(base+'_BUSER', 'out',
                                        '('+mkStr(base,'BUSER_WIDTH')+'-1)', 0, None, 0,
                                        True, True, mkStr(base,'BUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_BVALID', 'out',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_BREADY', 'in',
                                    None, None, None, None))

        if not lite:
            ret.append(self.mkPortEntry(base+'_ARID', 'in',
                                        '('+mkStr(base,'THREAD_ID_WIDTH')+'-1)', 0, None, 0,
                                        True, True, mkStr(base,'THREAD_ID_WIDTH')+' >0', 'true'))
        ret.append(self.mkPortEntry(base+'_ARADDR', 'in',
                                    '('+mkStr(base,'ADDR_WIDTH')+'-1)', addrwidth-1, None, 0))
        if not lite:
            ret.append(self.mkPortEntry(base+'_ARLEN', 'in',
                                        None, 7, None, 0))
            ret.append(self.mkPortEntry(base+'_ARSIZE', 'in',
                                        None, 2, None, 0))
            ret.append(self.mkPortEntry(base+'_ARBURST', 'in',
                                        None, 1, None, 0))
            ret.append(self.mkPortEntry(base+'_ARLOCK', 'in',
                                        None, 1, None, 0))
            ret.append(self.mkPortEntry(base+'_ARCACHE', 'in',
                                        None, 3, None, 0))
        ret.append(self.mkPortEntry(base+'_ARPROT', 'in',
                                    None, 2, None, 0))
        if not lite:
            ret.append(self.mkPortEntry(base+'_ARQOS', 'in',
                                        None, 3, None, 0))
            ret.append(self.mkPortEntry(base+'_ARUSER', 'in',
                                        '('+mkStr(base,'ARUSER_WIDTH')+'-1)', 0, None, 0,
                                        True, True, mkStr(base,'ARUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_ARVALID', 'in',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_ARREADY', 'out',
                                    None, None, None, None))

        if not lite:
            ret.append(self.mkPortEntry(base+'_RID', 'out',
                                        '('+mkStr(base,'THREAD_ID_WIDTH')+'-1)', 0, None, 0,
                                        True, True, mkStr(base,'THREAD_ID_WIDTH')+' >0', 'true'))
        ret.append(self.mkPortEntry(base+'_RDATA', 'out',
                                    '('+mkStr(base,'DATA_WIDTH')+'-1)', datawidth-1, None, 0))
        ret.append(self.mkPortEntry(base+'_RRESP', 'out',
                                    None, 1, None, 0))
        if not lite:
            ret.append(self.mkPortEntry(base+'_RLAST', 'out',
                                        None, None, None, None))
            ret.append(self.mkPortEntry(base+'_RUSER', 'out',
                                        '('+mkStr(base,'RUSER_WIDTH')+'-1)', 0, None, 0,
                                        True, True, mkStr(base,'RUSER_WIDTH')+' >0', 'false'))
        ret.append(self.mkPortEntry(base+'_RVALID', 'out',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_RREADY', 'in',
                                    None, None, None, None))

        ret.append(self.mkPortEntry(base+'_ACLK', 'in',
                                    None, None, None, None))
        ret.append(self.mkPortEntry(base+'_ARESETN', 'in',
                                    None, None, None, None))

        return ret
        
    def mkPortEntry(self, name, direction, lvar, lvalue, rvar, rvalue,
                    withdriver=False,
                    withextension=False, extensionvar=None, extensionvalue='true'):
        port = self.doc.createElement('spirit:port')
        port.appendChild(self.mkName(name))
        port.appendChild(self.mkWire(direction, lvar, lvalue, rvar, rvalue, withdriver))
        #if withextension:
        #    port.appendChild(self.mkPortVendorExtensions(lvar, extensionvalue))
        return port
        
    def mkWire(self, direction, lvar, lvalue, rvar, rvalue, withdriver=False):
        wire = self.doc.createElement('spirit:wire')
        wire.appendChild(self.mkDirection(direction))
        if not (lvalue is None and rvalue is None):
            wire.appendChild(self.mkVector(lvar, lvalue, rvar, rvalue))
        wire.appendChild(self.mkWireTypeDefs('wire'))
        if withdriver:
            wire.appendChild(self.mkDriver())
        return wire

    def mkDirection(self, direction):
        return self.mkTextNode('spirit:direction', direction)
        
    def mkVector(self, lvar, lvalue, rvar, rvalue):
        vector = self.doc.createElement('spirit:vector')
        lresolve = "immediate" if lvar is None else "dependent"
        rresolve = "immediate" if rvar is None else "dependent"
        left = self.doc.createElement('spirit:left')
        self.setAttribute(left, 'spirit:format', "long")
        self.setAttribute(left, 'spirit:resolve', lresolve)
        if lresolve == "dependent":
            self.setAttribute(left, 'spirit:dependency', lvar)
        self.setText(left, lvalue)
        vector.appendChild(left)
        right = self.doc.createElement('spirit:right')
        self.setAttribute(right, 'spirit:format', "long")
        self.setAttribute(right, 'spirit:resolve', rresolve)
        if rresolve == "dependent":
            self.setAttribute(right, 'spirit:dependency', rvar)
        self.setText(right, rvalue)
        vector.appendChild(right)
        return vector

    def mkWireTypeDefs(self, wiretype):
        wiretypedefs = self.doc.createElement('spirit:wireTypeDefs')
        wiretypedefs.appendChild(self.mkWireTypeDef(wiretype))
        return wiretypedefs
        
    def mkWireTypeDef(self, wiretype):
        wiretypedef = self.doc.createElement('spirit:wireTypeDef')
        wiretypedef.appendChild(self.mkTextNode('spirit:typeName', wiretype))
        wiretypedef.appendChild(self.mkTextNode('spirit:viewNameRef', 'xilinx_verilogsynthesis'))
        wiretypedef.appendChild(self.mkTextNode('spirit:viewNameRef', 'xilinx_verilogbehavioralsimulation'))
        return wiretypedef

    def mkDriver(self):
        driver = self.doc.createElement('spirit:driver')
        driver.appendChild(self.mkTextNode('spirit:defaultValue', 0))
        return driver

    def mkPortVendorExtensions(self, var, value='true'):
        extensions = self.doc.createElement('spirit:vendorExtensions')
        portinfo = self.doc.createElement('xilinx:portInfo')
        enablement = self.doc.createElement('xilinx:enablement')
        enablement.appendChild(self.mkTextNode('xilinx:presence', 'optional'))
        isEnabled = self.doc.createElement('xilinx:isEnabled')
        self.setAttribute(isEnabled, 'xilinx:resolve', "dependent")
        self.setAttribute(isEnabled, 'xilinx:dependency',
                          ("spirit:decode(id('MODELPARAM_VALUE." + var +
                           "')) >0"))
        self.setText(isEnabled, value)
        enablement.appendChild(isEnabled)
        portinfo.appendChild(enablement)
        extensions.appendChild(portinfo)
        return extensions
        
    #---------------------------------------------------------------------------
    def mkModelParameters(self):
        modelparameters = self.doc.createElement('spirit:modelParameters')
        order = 2
        
        for thread in self.threads:
            for memory in thread.memories:
                order, rslt = self.mkModelParameter(thread, memory, order)
                for p in rslt: modelparameters.appendChild(p)
            for instream in thread.instreams:
                order, rslt = self.mkModelParameter(thread, instream, order)
                for p in rslt: modelparameters.appendChild(p)
            for outstream in thread.outstreams:
                order, rslt = self.mkModelParameter(thread, outstream, order)
                for p in rslt: modelparameters.appendChild(p)
            for iochannel in thread.iochannels:
                order, rslt = self.mkModelParameter(thread, iochannel, order, lite=self.lite)
                for p in rslt: modelparameters.appendChild(p)
            for ioregister in thread.ioregisters:
                order, rslt = self.mkModelParameter(thread, ioregister, order, lite=self.lite)
                for p in rslt: modelparameters.appendChild(p)

        for paramname, paramlvalue, paramtype in self.ext_params:
            p = self.doc.createElement('spirit:modelParameter')
            p.appendChild(self.mkName(paramname))
            p.appendChild(self.mkTextNode('spirit:displayName', paramname))
            p.appendChild(self.mkTextNode('spirit:description', paramname))
            value = self.doc.createElement('spirit:value')
            if paramtype == 'integer':
                self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'generated')
            self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE." + paramname)
            self.setText(value, paramlvalue)
            p.appendChild(value)
            modelparameters.appendChild(p)
                
        return modelparameters

    def mkModelParameter(self, thread, obj, order, lite=False):
        ret = []
        name = thread.name + '_' + obj.name + '_AXI'
        
        if not lite:
            idwidth = self.doc.createElement('spirit:modelParameter')
            self.setAttribute(idwidth, 'spirit:dataType', "integer")
            idwidth.appendChild(self.mkName("C_" + name + "_THREAD_ID_WIDTH"))
            idwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_THREAD_ID_WIDTH"))
            idwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_THREAD_ID_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE.C_" + name + "_THREAD_ID_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_THREAD_ID_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_THREAD_ID_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "32")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 1)
            idwidth.appendChild(value)
            ret.append(idwidth)
            order += 1
    
        addrwidth = self.doc.createElement('spirit:modelParameter')
        self.setAttribute(addrwidth, 'spirit:dataType', "integer")
        addrwidth.appendChild(self.mkName("C_" + name + "_ADDR_WIDTH"))
        addrwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_ADDR_WIDTH"))
        addrwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_ADDR_WIDTH"))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:format', 'long')
        self.setAttribute(value, 'spirit:resolve', 'generated')
        self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE.C_" + name + "_ADDR_WIDTH")
        self.setAttribute(value, 'spirit:order', order)
        self.setAttribute(value, 'spirit:rangeType', "long")
        self.setText(value, self.ext_addrwidth)
        addrwidth.appendChild(value)
        ret.append(addrwidth)
        order += 1
    
        datawidth = self.doc.createElement('spirit:modelParameter')
        self.setAttribute(datawidth, 'spirit:dataType', "integer")
        datawidth.appendChild(self.mkName("C_" + name + "_DATA_WIDTH"))
        datawidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_DATA_WIDTH"))
        datawidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_DATA_WIDTH"))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:format', 'long')
        self.setAttribute(value, 'spirit:resolve', 'generated')
        self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE.C_" + name + "_DATA_WIDTH")
        self.setAttribute(value, 'spirit:order', order)
        self.setAttribute(value, 'spirit:rangeType', "long")
        self.setText(value, obj.ext_datawidth)
        datawidth.appendChild(value)
        ret.append(datawidth)
        order += 1

        if not lite:
            awuserwidth = self.doc.createElement('spirit:modelParameter')
            self.setAttribute(awuserwidth, 'spirit:dataType', "integer")
            awuserwidth.appendChild(self.mkName("C_" + name + "_AWUSER_WIDTH"))
            awuserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_AWUSER_WIDTH"))
            awuserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_AWUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE.C_" + name + "_AWUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_AWUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_AWUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 1)
            awuserwidth.appendChild(value)
            ret.append(awuserwidth)
            order += 1

        if not lite:
            aruserwidth = self.doc.createElement('spirit:modelParameter')
            self.setAttribute(aruserwidth, 'spirit:dataType', "integer")
            aruserwidth.appendChild(self.mkName("C_" + name + "_ARUSER_WIDTH"))
            aruserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_ARUSER_WIDTH"))
            aruserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_ARUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE.C_" + name + "_ARUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_ARUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_ARUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 1)
            aruserwidth.appendChild(value)
            ret.append(aruserwidth)
            order += 1
    
        if not lite:
            wuserwidth = self.doc.createElement('spirit:modelParameter')
            self.setAttribute(wuserwidth, 'spirit:dataType', "integer")
            wuserwidth.appendChild(self.mkName("C_" + name + "_WUSER_WIDTH"))
            wuserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_WUSER_WIDTH"))
            wuserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_WUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE.C_" + name + "_WUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_WUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_WUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 1)
            wuserwidth.appendChild(value)
            ret.append(wuserwidth)
            order += 1
    
        if not lite:
            ruserwidth = self.doc.createElement('spirit:modelParameter')
            self.setAttribute(ruserwidth, 'spirit:dataType', "integer")
            ruserwidth.appendChild(self.mkName("C_" + name + "_RUSER_WIDTH"))
            ruserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_RUSER_WIDTH"))
            ruserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_RUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE.C_" + name + "_RUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_RUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_RUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 1)
            ruserwidth.appendChild(value)
            ret.append(ruserwidth)
            order += 1
    
        if not lite:
            buserwidth = self.doc.createElement('spirit:modelParameter')
            self.setAttribute(buserwidth, 'spirit:dataType', "integer")
            buserwidth.appendChild(self.mkName("C_" + name + "_BUSER_WIDTH"))
            buserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_BUSER_WIDTH"))
            buserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_BUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "MODELPARAM_VALUE.C_" + name + "_BUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_BUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_BUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 1)
            buserwidth.appendChild(value)
            ret.append(buserwidth)
            order += 1
        
        return order, ret

    #---------------------------------------------------------------------------
    def mkChoices(self):
        choices = self.doc.createElement('spirit:choices')
        choices.appendChild(self.mkChoice('choices_0', (32, 64, 128, 256, 512) ))
        
        choices_1 = self.doc.createElement('spirit:choice')
        choices_1.appendChild(self.mkName('choices_1'))
        choices_1_true = self.doc.createElement('spirit:enumeration')
        self.setAttribute(choices_1_true, 'spirit:text', 'true')
        self.setText(choices_1_true, 1)
        choices_1_false = self.doc.createElement('spirit:enumeration')
        self.setAttribute(choices_1_false, 'spirit:text', 'false')
        self.setText(choices_1_false, 0)
        choices_1.appendChild(choices_1_true)
        choices_1.appendChild(choices_1_false)
        choices.appendChild(choices_1)

        choices.appendChild(self.mkChoice('choices_2', (32, 64, 128, 256, 512) ))
        
        choices_3 = self.doc.createElement('spirit:choice')
        choices_3.appendChild(self.mkName('choices_3'))
        choices_3_true = self.doc.createElement('spirit:enumeration')
        self.setAttribute(choices_3_true, 'spirit:text', 'true')
        self.setText(choices_3_true, 1)
        choices_3_false = self.doc.createElement('spirit:enumeration')
        self.setAttribute(choices_3_false, 'spirit:text', 'false')
        self.setText(choices_3_false, 0)
        choices_3.appendChild(choices_3_true)
        choices_3.appendChild(choices_3_false)
        choices.appendChild(choices_3)

        choices.appendChild(self.mkChoice('choices_4', (1, 2, 4, 8, 16, 32, 64, 128, 256, 512) ))
        choices.appendChild(self.mkChoice('choices_5', (1, 2, 4, 8, 16, 32, 64, 128, 256, 512) ))
        
        return choices

    def mkChoice(self, name, arg):
        choice = self.doc.createElement('spirit:choice')
        choice.appendChild(self.mkName(name))
        for a in arg:
            choice.appendChild(self.mkTextNode('spirit:enumeration', a))
        return choice
                
    #---------------------------------------------------------------------------
    def mkFileSets(self):
        filesets = self.doc.createElement('spirit:fileSets')
        source = self.doc.createElement('spirit:fileSet')
        source.appendChild(self.mkName("xilinx_verilogsynthesis_view_fileset"))
        source.appendChild(self.mkFileSet('hdl/verilog/pycoram_'+self.userlogic_name.lower()+'.v',
                                          'verilogSource'))
        filesets.appendChild(source)
        
        sim = self.doc.createElement('spirit:fileSet')
        sim.appendChild(self.mkName("xilinx_verilogbehavioralsimulation_view_fileset"))
        sim.appendChild(self.mkFileSet('hdl/verilog/pycoram_'+self.userlogic_name.lower()+'.v',
                                       'verilogSource'))
        sim.appendChild(self.mkFileSet('test/test_pycoram_'+self.userlogic_name.lower()+'.v',
                                       'verilogSource'))
        filesets.appendChild(sim)
        
        xguitcl = self.doc.createElement('spirit:fileSet')
        xguitcl.appendChild(self.mkName("xilinx_xpgui_view_fileset"))
        xguitcl.appendChild(self.mkFileSet('xgui/xgui.tcl',
                                           'tclSource', 'XGUI_VERSION_2'))
        filesets.appendChild(xguitcl)
        
        bdtcl = self.doc.createElement('spirit:fileSet')
        bdtcl.appendChild(self.mkName("bd_tcl_view_fileset"))
        bdtcl.appendChild(self.mkFileSet('bd/bd.tcl', 'tclSource'))
        filesets.appendChild(bdtcl)
        
        xdc = self.doc.createElement('spirit:fileSet')
        xdc.appendChild(self.mkName("xilinx_synthesisconstraints_view_fileset"))
        xdc.appendChild(self.mkFileSet('data/pycoram_'+self.userlogic_name.lower()+'.xdc',
                                       None, 'xdc'))
        filesets.appendChild(xdc)
        
        return filesets

    def mkFileSet(self, name, filetype=None, *userfiletypes):
        fileset = self.doc.createElement('spirit:file')
        fileset.appendChild(self.mkName(name))
        if filetype is not None:
            fileset.appendChild(self.mkTextNode('spirit:fileType', filetype))
        for u in userfiletypes:
            fileset.appendChild(self.mkTextNode('spirit:userFileType', u))
        return fileset

    #---------------------------------------------------------------------------
    def mkDescription(self):
        return self.mkTextNode('spirit:description', 'PyCoRAM IP-core')

    #---------------------------------------------------------------------------
    def mkParameters(self):
        parameters = self.doc.createElement('spirit:parameters')
        
        compname = self.doc.createElement('spirit:parameter')
        compname.appendChild(self.mkName('Component_Name'))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:resolve', 'user')
        self.setAttribute(value, 'spirit:id', "PARAM_VALUE." + 'Component_Name')
        self.setAttribute(value, 'spirit:order', 1)
        self.setText(value, 'pycoram_' + self.userlogic_name.lower() +'_v1_0')
        compname.appendChild(value)
        parameters.appendChild(compname)
        
        order = 2
        for thread in self.threads:
            for memory in thread.memories:
                order, rslt = self.mkParameter(thread, memory, order)
                for p in rslt: parameters.appendChild(p)
            for instream in thread.instreams:
                order, rslt = self.mkParameter(thread, instream, order)
                for p in rslt: parameters.appendChild(p)
            for outstream in thread.outstreams:
                order, rslt = self.mkParameter(thread, outstream, order)
                for p in rslt: parameters.appendChild(p)
            for iochannel in thread.iochannels:
                order, rslt = self.mkParameter(thread, iochannel, order, lite=self.lite)
                for p in rslt: parameters.appendChild(p)
            for ioregister in thread.ioregisters:
                order, rslt = self.mkParameter(thread, ioregister, order, lite=self.lite)
                for p in rslt: parameters.appendChild(p)
                
        for paramname, paramlvalue, paramtype in self.ext_params:
            p = self.doc.createElement('spirit:parameter')
            p.appendChild(self.mkName(paramname))
            p.appendChild(self.mkTextNode('spirit:displayName', paramname))
            p.appendChild(self.mkTextNode('spirit:description', paramname))
            value = self.doc.createElement('spirit:value')
            if paramtype == 'integer':
                self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'user')
            self.setAttribute(value, 'spirit:id', "PARAM_VALUE." + paramname)
            self.setText(value, paramlvalue)
            p.appendChild(value)
            parameters.appendChild(p)
            
        return parameters
    
    def mkParameter(self, thread, obj, order, lite=False):
        ret = []
        name = thread.name + '_' + obj.name + '_AXI'
        
        if not lite:
            idwidth = self.doc.createElement('spirit:parameter')
            idwidth.appendChild(self.mkName("C_" + name + "_THREAD_ID_WIDTH"))
            idwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_THREAD_ID_WIDTH"))
            idwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_THREAD_ID_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'user')
            self.setAttribute(value, 'spirit:id', "PARAM_VALUE.C_" + name + "_THREAD_ID_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_THREAD_ID_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_THREAD_ID_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "32")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 1)
            idwidth.appendChild(value)
            ret.append(idwidth)
            order += 1
    
        addrwidth = self.doc.createElement('spirit:parameter')
        addrwidth.appendChild(self.mkName("C_" + name + "_ADDR_WIDTH"))
        addrwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_ADDR_WIDTH"))
        addrwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_ADDR_WIDTH"))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:format', 'long')
        self.setAttribute(value, 'spirit:resolve', 'user')
        self.setAttribute(value, 'spirit:id', "PARAM_VALUE.C_" + name + "_ADDR_WIDTH")
        self.setAttribute(value, 'spirit:order', order)
        self.setAttribute(value, 'spirit:rangeType', "long")
        self.setText(value, self.ext_addrwidth)
        addrwidth.appendChild(value)
        extensions = self.doc.createElement('spirit:vendorExtensions')
        parameterinfo = self.doc.createElement('xilinx:parameterInfo')
        enablement = self.doc.createElement('xilinx:enablement')
        enablement.appendChild(self.mkTextNode('xilinx:isEnabled', 'false'))
        parameterinfo.appendChild(enablement)
        extensions.appendChild(parameterinfo)
        addrwidth.appendChild(extensions)
        ret.append(addrwidth)
        order += 1
    
        datawidth = self.doc.createElement('spirit:parameter')
        datawidth.appendChild(self.mkName("C_" + name + "_DATA_WIDTH"))
        datawidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_DATA_WIDTH"))
        datawidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_DATA_WIDTH"))
        value = self.doc.createElement('spirit:value')
        self.setAttribute(value, 'spirit:format', 'long')
        self.setAttribute(value, 'spirit:resolve', 'user')
        self.setAttribute(value, 'spirit:id', "PARAM_VALUE.C_" + name + "_DATA_WIDTH")
        self.setAttribute(value, 'spirit:order', order)
        self.setAttribute(value, 'spirit:rangeType', "long")
        self.setText(value, obj.ext_datawidth)
        datawidth.appendChild(value)
        extensions = self.doc.createElement('spirit:vendorExtensions')
        parameterinfo = self.doc.createElement('xilinx:parameterInfo')
        enablement = self.doc.createElement('xilinx:enablement')
        enablement.appendChild(self.mkTextNode('xilinx:isEnabled', 'false'))
        parameterinfo.appendChild(enablement)
        extensions.appendChild(parameterinfo)
        datawidth.appendChild(extensions)
        ret.append(datawidth)
        order += 1

        if not lite:
            awuserwidth = self.doc.createElement('spirit:parameter')
            awuserwidth.appendChild(self.mkName("C_" + name + "_AWUSER_WIDTH"))
            awuserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_AWUSER_WIDTH"))
            awuserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_AWUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "PARAM_VALUE.C_" + name + "_AWUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_AWUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_AWUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 0)
            awuserwidth.appendChild(value)
            ret.append(awuserwidth)
            order += 1

        if not lite:
            aruserwidth = self.doc.createElement('spirit:parameter')
            aruserwidth.appendChild(self.mkName("C_" + name + "_ARUSER_WIDTH"))
            aruserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_ARUSER_WIDTH"))
            aruserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_ARUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "PARAM_VALUE.C_" + name + "_ARUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_ARUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_ARUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 0)
            aruserwidth.appendChild(value)
            ret.append(aruserwidth)
            order += 1
    
        if not lite:
            wuserwidth = self.doc.createElement('spirit:parameter')
            wuserwidth.appendChild(self.mkName("C_" + name + "_WUSER_WIDTH"))
            wuserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_WUSER_WIDTH"))
            wuserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_WUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "PARAM_VALUE.C_" + name + "_WUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_WUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_WUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 0)
            wuserwidth.appendChild(value)
            ret.append(wuserwidth)
            order += 1
    
        if not lite:
            ruserwidth = self.doc.createElement('spirit:parameter')
            ruserwidth.appendChild(self.mkName("C_" + name + "_RUSER_WIDTH"))
            ruserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_RUSER_WIDTH"))
            ruserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_RUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "PARAM_VALUE.C_" + name + "_RUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_RUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_RUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 0)
            ruserwidth.appendChild(value)
            ret.append(ruserwidth)
            order += 1
    
        if not lite:
            buserwidth = self.doc.createElement('spirit:parameter')
            buserwidth.appendChild(self.mkName("C_" + name + "_BUSER_WIDTH"))
            buserwidth.appendChild(self.mkTextNode('spirit:displayName', "C_" + name + "_BUSER_WIDTH"))
            buserwidth.appendChild(self.mkTextNode('spirit:description', "C_" + name + "_BUSER_WIDTH"))
            value = self.doc.createElement('spirit:value')
            self.setAttribute(value, 'spirit:format', 'long')
            self.setAttribute(value, 'spirit:resolve', 'dependent')
            self.setAttribute(value, 'spirit:id', "PARAM_VALUE.C_" + name + "_BUSER_WIDTH")
            self.setAttribute(value, 'spirit:dependency',
                              ("((spirit:decode(id('PARAM_VALUE.C_" + name +
                               "_BUSER_WIDTH')) <= 0 ) + (spirit:decode(id('PARAM_VALUE.C_" +
                               name + "_BUSER_WIDTH'))))"))
            self.setAttribute(value, 'spirit:order', order)
            self.setAttribute(value, 'spirit:minimum', "0")
            self.setAttribute(value, 'spirit:maximum', "1024")
            self.setAttribute(value, 'spirit:rangeType', "long")
            self.setText(value, 0)
            buserwidth.appendChild(value)
            ret.append(buserwidth)
            order += 1
        
        return order, ret

    #---------------------------------------------------------------------------
    def mkVendorExtensions(self):
        extensions = self.doc.createElement('spirit:vendorExtensions')
        extensions.appendChild(self.mkCoreExtensions())
        packageinfo = self.doc.createElement('xilinx:packagingInfo')
        packageinfo.appendChild(self.mkTextNode('xilinx:xilinxVersion', '2014.4'))
        extensions.appendChild(packageinfo)
        return extensions

    def mkCoreExtensions(self):
        coreextensions = self.doc.createElement('xilinx:coreExtensions')
        supported = self.doc.createElement('xilinx:supportedFamilies')
        family = self.doc.createElement('xilinx:family')
        self.setAttribute(family, 'xilinx:lifeCycle', 'Production')
        self.setText(family, 'zynq')
        supported.appendChild(family)
        coreextensions.appendChild(supported)
        taxonomies = self.doc.createElement('xilinx:taxonomies')
        taxonomies.appendChild(self.mkTextNode('xilinx:taxonomy', 'AXI_Peripheral'))
        coreextensions.appendChild(taxonomies)
        coreextensions.appendChild(self.mkTextNode('xilinx:displayName',
                                                   ('pycoram_' + self.userlogic_name.lower() +
                                                    '_v1_0')))
        #coreextensions.appendChild(self.mkTextNode('xilinx:coreRevison', 1))
        #now = datetime.datetime.now()
        #dt = now.strftime("%Y-%m-%d") # '2015-03-08T02:16:15Z'
        #coreextensions.appendChild(self.mkTextNode('xilinx:coreCreationDateTime', dt))
        return coreextensions

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    gen = ComponentGen()
    rslt = gen.generate('userlogic', ())
    print(rslt)




