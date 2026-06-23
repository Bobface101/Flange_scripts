## For Mod E., Type 01 GOST flanges

import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'Mod_E_Type_01_Data.csv')
output_file = os.path.join(script_dir, 'commands.scr')
scr_lines = []
START_DRAWING_POSITION = (0,-10000)

def fmt(pt):
    """format point as an AutoCAD coordinate string."""
    x, y = pt
    return f"{x:g},{y:g}"

def midpoint(*points):   
    num_points = len(points)
    x_avg = sum(p[0] for p in points) / num_points
    y_avg = sum(p[1] for p in points) / num_points
    return (x_avg, y_avg)

def conjugate(pt): # reflects point in mirror line of FLANGE, not x-axis
    x, y = pt
    return(x, 2*sy-y)

def symmetric_diameter_dim(extent, offset):
        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(extent))
        scr_lines.append(fmt(conjugate(extent))) # symmetrical diameter
        scr_lines.append("T") # text edit 
        scr_lines.append("%%c<>") 
        scr_lines.append(fmt(((L[0]+offset),(L[1])))) 

def draw_roughness_symbol(startpos, sidelength):
        h = sidelength * (3**0.5 / 2)
        p_left = (startpos[0] - sidelength / 2, startpos[1] + h)
        p_right = (startpos[0] + sidelength / 2, startpos[1] + h)
        p_ext = (startpos[0] + sidelength, startpos[1] + 2 * h)

        scr_lines.append("LINE")
        scr_lines.append(fmt(p_left))
        scr_lines.append(fmt(startpos))
        scr_lines.append(fmt(p_ext))
        scr_lines.append("")

        scr_lines.append("LINE")
        scr_lines.append(fmt(p_left))
        scr_lines.append(fmt(p_right))
        scr_lines.append("")

def draw_check_mark(startpos, sidelength):
    x, y = startpos
    s = sidelength

    def draw_arc(p1, p2, p3):
        scr_lines.append("ARC")
        scr_lines.append(fmt(p1))
        scr_lines.append(fmt(p2))
        scr_lines.append(fmt(p3))

    # Check mark
    scr_lines.append("LINE")
    scr_lines.append(fmt((x - 0.3 * s, y + 0.5 * s)))
    scr_lines.append(fmt((x - 0.1 * s, y + 0.3 * s)))
    scr_lines.append(fmt((x + 0.4 * s, y + 0.8 * s)))
    scr_lines.append("")

    #brackets
    draw_arc((x - 0.7 * s, y + s), (x - 0.95 * s, y + 0.5 * s), (x - 0.7 * s, y))
    draw_arc((x + 0.7 * s, y + s), (x + 0.95 * s, y + 0.5 * s), (x + 0.7 * s, y))


def add_sysvar(name, value):
    """Add a system variable setting to the script.
      VARNAME
      value
    """
    scr_lines.append(name)
    scr_lines.append(str(value))


with open(input_file, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)#skip header


    # random settings to make the script be able to do everything itself
    add_sysvar("VTENABLE", 0)
    add_sysvar("DYNMODE", 0)
    add_sysvar("CMDECHO", 0)
    add_sysvar("OSMODE", 0)
    add_sysvar("ATTDIA", 0)
    add_sysvar("ATTREQ", 1)
    scr_lines.append("VIEWRES")
    scr_lines.append("Y")
    scr_lines.append("20000")
    scr_lines.append("TEXTSTYLE")
    scr_lines.append("ROMANS")

    gx, gy = START_DRAWING_POSITION # this is the bottom left hand corner of the current drawing

    #start reading individual flanges here
    for row in reader:

        flange = row[0]
        d_b   = float(row[1])
        b  = float(row[2])
        OD  = float(row[3])
        D1 = float(row[4])
        d   = float(row[5])
        n   = int(row[6])
        bolt_size   = row[7]
        D4   = float(row[8])
        h1 = float(row[9])

        gost_scales = [1, 2, 2.5, 4, 5, 10, 15, 20]
        
        #find a scale which fits in the space
        dimscale = 1  # Default to 1:1
        for scale in gost_scales:
            if OD / scale <= 105.0:
                dimscale = scale
                break
        
        #set global dimscale to the correct one
        add_sysvar("DIMSCALE", dimscale)
        add_sysvar("LTSCALE", 1/dimscale)

        gx += 200*dimscale # update in halves like this so it looks pretty 

        sx = gx + 100*dimscale
        sy = gy + 220*dimscale

        # Calculate points with startpos offset
        A =  (sx,         sy)
        B  = (sx + 0,     sy + OD / 2)
        C  = (sx + b - h1, sy + OD / 2)
        D = (sx + b - h1, sy + (D1 / 2) + d / 2)  
        E  = (sx + 0,     sy + (D1 / 2) + d / 2)
        F  = (sx + b - h1, sy + (D1 / 2) - d / 2)
        G  = (sx + 0,     sy + (D1 / 2) - d / 2)
        H  = (sx + 0,     sy + d_b / 2)
        I  = (sx + b,     sy + d_b / 2)
        J  = (sx + b,     sy + D4 / 2)
        K  = (sx + b - h1, sy + D4 / 2) 
        L =  (sx + b,     sy)

        # bounding box for crossing selection & zoom
        all_y = [B[1], C[1], D[1], E[1], F[1], G[1], H[1], I[1], J[1], K[1]]
        min_y = min(all_y)
        max_y = max(all_y)

        sel_x1 = sx - 1
        sel_y1 = min_y - 1
        sel_x2 = sx + b + 1
        sel_y2 = max_y + 1

        #Zoom to the area for this flange
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((sel_x1, 2*sy-(max_y + 1))))
        scr_lines.append(fmt((sel_x2, sel_y2)))

        #Change to 0 layer
        scr_lines.append("CLAYER")
        scr_lines.append("0")

        #Write title 
        scr_lines.append("TEXT")
        scr_lines.append(fmt((gx+75, gy + 305*dimscale)))
        scr_lines.append(f"{20*dimscale}")
        scr_lines.append("0")
        scr_lines.append(f"{flange}")
        scr_lines.append("\n\n")

        #--- Draw line segments

        #  A -> H -> B -> C -> D -> E
        scr_lines.append("LINE")
        scr_lines.append(fmt(A))
        scr_lines.append(fmt(H))
        scr_lines.append(fmt(B))
        scr_lines.append(fmt(C))
        scr_lines.append(fmt(D))
        scr_lines.append(fmt(E))
        scr_lines.append("")  # Enter to end LINE command

        #  G -> F
        scr_lines.append("LINE")
        scr_lines.append(fmt(G))
        scr_lines.append(fmt(F))
        scr_lines.append("")  # Enter to end LINE command

        #  I -> L 
        scr_lines.append("LINE")
        scr_lines.append(fmt(I))
        scr_lines.append(fmt(L))
        scr_lines.append("")  # Enter to end LINE command


        #normal case: no overlap, draw full chain # for type E, this is always the case
        scr_lines.append("LINE")
        scr_lines.append(fmt(D))
        scr_lines.append(fmt(F))
        scr_lines.append(fmt(K))
        scr_lines.append(fmt(J))
        scr_lines.append(fmt(I))
        scr_lines.append(fmt(H))
        scr_lines.append("")  # Enter to end LINE command

        #Change to DIM layer
        scr_lines.append("CLAYER")
        scr_lines.append("DIM")
        
        # Hatching 
        add_sysvar("HPNAME", "ANSI31")
        add_sysvar("HPSCALE", 10*dimscale)
        add_sysvar("HPANG", 0)

        scr_lines.append("-HATCH")
        scr_lines.append(fmt(midpoint(B,C,D,E)))
        scr_lines.append(fmt(midpoint(F,G,H,I)))
        scr_lines.append("")   
        

        # --- Mirror 
        scr_lines.append("MIRROR")
        scr_lines.append("C")                          # Crossing selection
        scr_lines.append(fmt((sel_x1, sel_y1)))         # First corner
        scr_lines.append(fmt((sel_x2, sel_y2)))         # Opposite corner
        scr_lines.append("")                            # Enter to end selection
        scr_lines.append(fmt((sx, sy)))                  # First point of mirror line (x-axis)
        scr_lines.append(fmt((sx + 1, sy)))              # Second point of mirror line
        scr_lines.append("N")                           # Don't erase source objects

        # Centerlines 
        #Change to centerline layer
        scr_lines.append("CLAYER")
        scr_lines.append("CENTER")
        add_sysvar("CELWEIGHT", 5) #scale centerline weight, scale, extension
        add_sysvar("CENTERLTSCALE", 25*dimscale)
        add_sysvar("CENTEREXE", 1.0*dimscale)

        #zoom in so it doesn't get fucked up
        add_sysvar("PICKBOX", 1)
        groove_margin = 2
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((E[0] - groove_margin, G[1] - groove_margin)))
        scr_lines.append(fmt((D[0] + groove_margin, D[1] + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(E, D)))
        scr_lines.append(fmt(midpoint(G, F)))

        # bottom half
        cE = conjugate(E); cD = conjugate(D)
        cG = conjugate(G); cF = conjugate(F)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((cE[0] - groove_margin, min(cE[1], cG[1]) - groove_margin)))
        scr_lines.append(fmt((cD[0] + groove_margin, max(cD[1], cG[1]) + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(cE, cD)))
        scr_lines.append(fmt(midpoint(cG, cF)))

        # main centerline
        cH = conjugate(H); cI = conjugate(I)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((H[0] - groove_margin, min(H[1], cH[1]) - groove_margin)))
        scr_lines.append(fmt((I[0] + groove_margin, max(H[1], cH[1]) + groove_margin)))

        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(H, I)))
        scr_lines.append(fmt(midpoint(cH, cI)))

        #zoom back out
        add_sysvar("PICKBOX", 3)
        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((sel_x1, 2*sy-(max_y + 1))))
        scr_lines.append(fmt((sel_x2, sel_y2)))
        
        #reset to default for hatch and dims
        add_sysvar("CELWEIGHT", -1) 
        add_sysvar("CELTSCALE", 1)

        ###
        scr_lines.append("CLAYER") # switch back 
        scr_lines.append("DIM")


        # DIMS
        SPACING = 6.5*dimscale

        # main symmetric
        symmetric_diameter_dim(I, SPACING)
        symmetric_diameter_dim(J, 2*SPACING)
        symmetric_diameter_dim(midpoint(D,F),3*SPACING)
        symmetric_diameter_dim(C,4*SPACING)

        # bolt 
        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(E))
        scr_lines.append(fmt(G)) 
        scr_lines.append("T") # text edit 
        scr_lines.append(f"%%c<> for {bolt_size}\X{n} holes") 
        temp = midpoint(E,G)
        scr_lines.append(fmt(((temp[0]-SPACING),(temp[1])))) 

        # thickness b and h
        scr_lines.append("DIMLINEAR") 
        scr_lines.append(fmt(conjugate(B))) # main flange thickness
        scr_lines.append(fmt(conjugate(C))) 
        temp = midpoint(conjugate(B),conjugate(C))
        scr_lines.append(fmt(((temp[0]),(temp[1]-2*SPACING)))) 

        scr_lines.append("DIMLINEAR")
        scr_lines.append(fmt(conjugate(C))) #notch dim
        scr_lines.append(fmt(conjugate(J))) 
        temp = (conjugate(C)[0] + h1/2, conjugate(C)[1])
        scr_lines.append(fmt(((temp[0]),(temp[1]-1*SPACING)))) 

        # leaders

        #leader1
        scr_lines.append("LEADER")
        scr_lines.append(fmt(midpoint(I,J)))
        q = (J[0]+SPACING*2.5,sy+(OD/2)+SPACING*0.5)
        scr_lines.append(fmt(q))
        scr_lines.append("")
        scr_lines.append("Ra 12,5")
        scr_lines.append("")

        # roughness symbol (face1)
        SIDELENGTH = 3.5*dimscale
        r = (q[0]+25*dimscale,q[1]+1.25*dimscale)
        draw_roughness_symbol(r, SIDELENGTH)

        #leader2
        scr_lines.append("LEADER")
        scr_lines.append(fmt(midpoint(K,J)))
        q = (J[0]+SPACING*1.5,sy+(OD/2)+SPACING*1.5)
        scr_lines.append(fmt(q))
        scr_lines.append("")
        scr_lines.append("Ra 25")
        scr_lines.append("")

        # roughness symbol (face2)
        SIDELENGTH = 3.5*dimscale
        r = (q[0]+20*dimscale,q[1]+1.25*dimscale)
        draw_roughness_symbol(r, SIDELENGTH)

        

        # global roughness 
        scr_lines.append("TEXT")
        p = (gx+165*dimscale, gy+282.675*dimscale)
        scr_lines.append(fmt(p))
        scr_lines.append(f"{3.5*dimscale}")
        scr_lines.append("0")
        scr_lines.append("Rz 100")
        scr_lines.append("\n\n")

        #symbols
        draw_roughness_symbol((p[0] + 24.75*dimscale, p[1]), SIDELENGTH)
        draw_check_mark((p[0] + 33*dimscale, p[1]), SIDELENGTH*1.25)
        
        #drawing template
        scr_lines.append("-INSERT")
        scr_lines.append("gost_flange_template")  
        scr_lines.append(fmt((gx, gy))) # corner in bottom left at relative 0,0     
        
        #scale it
        scr_lines.append(str(dimscale))            # x
        scr_lines.append(str(dimscale))            # Y 
        scr_lines.append("0")       # rotation
        
        #attributes
        scr_lines.append(f"{flange[0:5]}, {flange[6:]} Type01 Mod.E - GOST 33259-2015")
        scr_lines.append(f"{flange[0:5]}, {flange[6:]} Тип01 Исп.E - ГОСТ 33259-2015")
        scr_lines.append(f"1:{dimscale}")    #scale
        scr_lines.append(f"{flange[2:5]}-{flange[8:]}-01-E-09G2S GOST 33259-2015")
        
        #name
        scr_lines.append("TEXT")
        scr_lines.append(fmt((gx-0*dimscale, gy-5*dimscale)))
        scr_lines.append(f"{3.5*dimscale}")
        scr_lines.append("0")
        scr_lines.append("K. Flores")
        scr_lines.append("\n\n")

        # Update startpos for next shape
        gx += 200*dimscale
    
    #series label
    scr_lines.append("TEXT")
    scr_lines.append(fmt(START_DRAWING_POSITION))
    scr_lines.append(f"{500}")
    scr_lines.append("90")
    scr_lines.append("Mod. E Type 01")
    scr_lines.append("\n\n")

    # 
    scr_lines.append("ZOOM")
    scr_lines.append("E")
    # Restore defaults
    add_sysvar("CMDECHO", 1)
    add_sysvar("DYNMODE", 3)
    add_sysvar("OSMODE", 4133)

# 'a' to append to the commands
# 'utf-8' (NO -sig) prevents corrupting the middle of the file
with open(output_file, 'a', encoding='utf-8') as f:
    f.write('\n'.join(scr_lines))
    f.write('\n')
