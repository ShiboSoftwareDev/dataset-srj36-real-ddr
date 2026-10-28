import json, pathlib, math, re, hashlib, fnmatch, collections
from kicad_source import ROOT, components, one, many, parse

REFS = {'h3':['U1','DU1'], 'a64':['U1','U2','U3'], 'stmp157':['U1','U2','U3'], 'orangecrab':['U3','U4'], 'a13':['U100','U200']}

def extract(board):
    bid = board['id']
    tree = json.loads((ROOT/'.source-cache'/(bid+'.parsed.json')).read_text())
    nets = {n[1]:n[2] for n in many(tree,'net')}
    def netname(node):
        net = one(node,'net')
        if not net: return None
        return nets.get(net[0], net[-1]) if net[0]!='0' else None
    layers = [l for l in one(tree,'layers') if l[2] in ['signal','power','mixed']]
    layer_map = {l[1]:('top' if i==0 else 'bottom' if i==len(layers)-1 else f'inner{i}') for i,l in enumerate(layers)}
    signal_layers = [layer_map[l[1]] for l in layers if l[2]!='power']
    cs = components(tree)
    obstacles, pads = [], []
    approximations = collections.Counter()
    for component in cs:
        fp = component['node']; ref = component['ref']; at = component['at']
        if at is None: continue
        fx, fy = map(float,at[:2]); angle = math.radians(float(at[2]) if len(at)>2 else 0)
        for i,pad in enumerate(many(fp,'pad')):
            raw_layers = one(pad,'layers',[])
            ls = list(layer_map.values()) if '*.Cu' in raw_layers or 'F&B.Cu' in raw_layers else [layer_map[l] for l in raw_layers if l in layer_map]
            if not ls: continue
            pa = one(pad,'at',['0','0']); px,py = map(float,pa[:2]); size=one(pad,'size')
            if size is None: raise ValueError(f'{bid} pad without size {ref}.{pad[1]}')
            width,height = map(float,size[:2]); x=fx+px*math.cos(angle)+py*math.sin(angle); y=-fy+px*math.sin(angle)-py*math.cos(angle)
            name=netname(pad); port=f'{ref}.{pad[1]}'; oid=f'{port}.{i}'; shape=pad[3]; rotation=float(pa[2]) if len(pa)>2 else 0
            connected=[f'net:{name}',port] if name else []
            obstacle={'obstacleId':oid,'componentId':ref,'type':'rect','layers':ls,'center':{'x':x,'y':y},'width':width,'height':height,'connectedTo':connected}
            if shape=='circle' and abs(width-height)<1e-7: obstacle['shape']='circle'
            else:
                obstacle['ccwRotationDegrees']=rotation
                if shape not in ['rect','circle']: approximations[shape]+=1
            if pad[2]=='np_thru_hole':
                obstacle['isNonPlatedHole']=True;obstacle['connectedTo']=[]
            else:
                obstacle['circuitJsonMetadata']={('pcb_smtpad_id' if len(ls)==1 else 'pcb_plated_hole_id'):oid,'pcb_port_id':port,'source_component_name':ref,'source_port_name':pad[1]}
                pads.append({'ref':ref,'port':port,'net':name,'x':x,'y':y,'layers':ls,'obstacleId':oid})
            obstacles.append(obstacle)
    def is_signal(name):
        if not name or re.search(r'VREF|ZQ|VCC|VDD|GND|unconnected',name,re.I): return False
        if bid in ['a64','stmp157']: return name.startswith('/S0S')
        if bid=='orangecrab': return name.startswith('RAM_')
        return name.startswith('/DDR3')
    ic_nets={p['net'] for p in pads if p['ref'] in REFS[bid] and is_signal(p['net'])}
    selected=[]
    for name in sorted(ic_nets):
        points=[p for p in pads if p['net']==name]
        unique={p['port']:p for p in points}
        if len(unique)>=2: selected.append((name,list(unique.values())))
    project_path=ROOT/'.source-cache'/(bid+'.kicad_pro')
    project=json.loads(project_path.read_text()) if project_path.exists() else {}
    settings=project.get('net_settings',{}); project_rules=project.get('board',{}).get('design_settings',{}).get('rules',{})
    classes={}; assigned={}
    for c in many(tree,'net_class'):
        cl={k:float(one(c,k)[0]) for k in ['clearance','trace_width','via_dia','via_drill'] if one(c,k)}
        classes[c[1]]=cl
        for n in many(c,'add_net'): assigned[n[1]]=c[1]
    for c in settings.get('classes',[]):
        classes[c['name']]={'clearance':c['clearance'],'trace_width':c['track_width'],'via_dia':c['via_diameter'],'via_drill':c['via_drill']}
        for n in c.get('nets',[]):assigned[n]=c['name']
    for name,_ in selected:
        for pattern in settings.get('netclass_patterns',[]):
            if fnmatch.fnmatchcase(name,pattern['pattern']): assigned[name]=pattern['netclass'];break
    def rules(name):return classes[assigned.get(name,'Default')]
    clearances=[rules(n)['clearance'] for n,_ in selected]
    signal_vias=[v for v in many(tree,'via') if netname(v) in {n for n,_ in selected}]
    via_sizes=[float(one(v,'size')[0]) for v in signal_vias if one(v,'size')]
    via_drills=[float(one(v,'drill')[0]) for v in signal_vias if one(v,'drill')]
    # Legacy files often retain obsolete netclass via sizes. Use the smaller
    # existing manufactured DDR geometry, recording this normalization below.
    via_pad=min(via_sizes) if via_sizes else min(rules(n)['via_dia'] for n,_ in selected)
    via_hole=min(via_drills) if via_drills else min(rules(n)['via_drill'] for n,_ in selected)
    clearance=max(clearances)
    widths=[rules(n)['trace_width'] for n,_ in selected]
    edge=[]
    for key in ['gr_line','gr_arc','gr_rect','gr_poly']:
        for shape in many(tree,key):
            if one(shape,'layer')!=['Edge.Cuts']:continue
            for k in ['start','end','mid','center']:
                p=one(shape,k)
                if p:edge.append((float(p[0]),-float(p[1])))
            for pts in many(shape,'pts'):
                edge.extend((float(p[1]),-float(p[2])) for p in many(pts,'xy'))
    for c in cs:
        if c['at'] is None: continue
        fx,fy=map(float,c['at'][:2]);a=math.radians(float(c['at'][2]) if len(c['at'])>2 else 0)
        for key in ['fp_line','fp_arc','fp_rect','fp_poly']:
            for shape in many(c['node'],key):
                if one(shape,'layer')!=['Edge.Cuts']:continue
                for k in ['start','end','mid','center']:
                    p=one(shape,k)
                    if p:
                        x,y=map(float,p[:2]);edge.append((fx+x*math.cos(a)+y*math.sin(a),-fy+x*math.sin(a)-y*math.cos(a)))
    if not edge: raise ValueError(f'{bid} has no board edge')
    bounds={'minX':min(x for x,y in edge),'maxX':max(x for x,y in edge),'minY':min(y for x,y in edge),'maxY':max(y for x,y in edge)}
    connections=[]
    for name,ps in selected:
        connections.append({'name':name,'nominalTraceWidth':rules(name)['trace_width'],'pointsToConnect':[{'x':p['x'],'y':p['y'],'layer':p['layers'][0],'pointId':p['port'],'pcb_port_id':p['port'],'port_selector':p['port']} if len(p['layers'])==1 else {'x':p['x'],'y':p['y'],'layers':p['layers'],'pointId':p['port'],'pcb_port_id':p['port'],'port_selector':p['port']} for p in ps]})
        for o in obstacles:
            if f'net:{name}' in o['connectedTo']:o['connectedTo'].append(name)
    srj={'layerCount':len(layers),'minTraceWidth':min(widths),'minViaPadDiameter':via_pad,'minViaHoleDiameter':via_hole,'defaultObstacleMargin':clearance,'minTraceToPadEdgeClearance':clearance,'minViaEdgeToPadEdgeClearance':clearance,'minTraceToHoleEdgeClearance':project_rules.get('min_hole_clearance',clearance),'minViaHoleEdgeToViaHoleEdgeClearance':project_rules.get('min_hole_to_hole',clearance),'minBoardEdgeClearance':project_rules.get('min_copper_edge_clearance',0),'allowBlindAndBuriedVias':False,'allowViaInPad':False,'bounds':bounds,'obstacles':obstacles,'connections':connections,'buses':[{'busId':'ddr_signal_layers','name':'DDR source signal layers','connectionNames':[c['name'] for c in connections],'allowedLayers':signal_layers}]}
    metadata={**board,'sourceSha256':hashlib.sha256((ROOT/'.source-cache'/(bid+'.kicad_pcb')).read_bytes()).hexdigest(),'components':[{k:v for k,v in c.items() if k!='node'} for c in cs if c['ref'] in REFS[bid]],'nativeLayers':layers,'signalLayers':signal_layers,'nets':len(connections),'terminals':sum(len(c['pointsToConnect']) for c in connections),'pads':len(obstacles),'rules':{'widths':sorted(set(widths)),'clearances':sorted(set(clearances)),'appliedGlobalClearance':clearance,'viaPad':via_pad,'viaDrill':via_hole},'rectangularPadApproximations':dict(approximations),'scope':'All named DDR signal nets incident to CPU or RAM, including passive endpoints. Power, VREF, ZQ and unconnected nets excluded. Existing traces, vias and zones removed. Board uses edge bounding box. No timing or impedance constraints invented.'}
    manifest = json.loads((ROOT/'manifest.json').read_text())
    sample = next(item for item in manifest['samples'] if item['boardId'] == bid)
    rendered = json.dumps(srj, indent=2).encode()
    actual = hashlib.sha256(rendered).hexdigest()
    if actual != sample['sha256']:
        raise ValueError(f"{bid}: regenerated SHA-256 {actual} differs from captured {sample['sha256']}")
    (ROOT/sample['file']).write_bytes(rendered)
    print(f"{sample['id']} {bid}: regenerated exact captured input ({len(connections)} nets)")

for board in json.loads((ROOT/'provenance/source-boards.json').read_text()):
    raw = (ROOT/'.source-cache'/(board['id']+'.kicad_pcb')).read_bytes()
    provenance = next(json.loads(path.read_text()) for path in (ROOT/'provenance').glob('sample???.json') if json.loads(path.read_text())['id'] == board['id'])
    if hashlib.sha256(raw).hexdigest() != provenance['sourceSha256']:
        raise ValueError(f"{board['id']}: source PCB hash mismatch")
    (ROOT/'.source-cache'/(board['id']+'.parsed.json')).write_text(json.dumps(parse(raw.decode())))
    extract(board)
