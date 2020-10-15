import sys, string
from xml.dom import minidom, Node
import pprint
import types



def walk(node):
    nodeData = {}
    
    if node.nodeType == Node.ELEMENT_NODE:

        # Walk over any text nodes in the current node.
        nodeContent = getText(node)
        if nodeContent is not None:
            # It's a text node. Should have no children
            nodeData = nodeContent
        else:
            nodeAttrMap = getAttrs(node)
            nodeData.update(nodeAttrMap)

            # Walk the child nodes.
            for child in node.childNodes:
                childData = walk(child)

                for key, value in childData.items():
                    if not nodeData.has_key(key):
                        nodeData[key] = value
                    elif type(nodeData.get(key)) == types.ListType:
                        nodeData[key].append(value)
                    else:
                        nodeData[key] = [nodeData.get(key), value]
                        pass
                    continue
                
                continue
            pass
        pass

    nodeMap = {node.nodeName: nodeData}
    if node.nodeName == '#text':
        nodeMap = {}
    return nodeMap
## END walk


def getAttrs(node):
    # Write out the attributes.
    attrMap = {}
    attrs = node.attributes
    for attrName in attrs.keys():
        attrNode = attrs.get(attrName)
        attrName = attrNode.nodeName
        attrValue = attrNode.nodeValue
        attrMap[attrName] = attrValue
        continue
    return attrMap
## END getAttr

def getText(node):
    # Walk over any text nodes in the current node.
    content = []
    for child in node.childNodes:
        if child.nodeType == Node.TEXT_NODE:
            content.append(child.nodeValue)
            pass
        continue

    contentText = None
    if content:
        strContent = string.join(content).strip()
        if len(strContent):
            contentText = strContent
            pass
        pass
    return contentText
## END getText


def parseXml(xmlfile=None, xmldata=None):
    if xmlfile is not None:
        dom = minidom.parse(xmlfile)
    elif xmldata is not None:
        dom = minidom.parseString(xmldata)
    else:
        print "parseXml: you must provide either a pathname or a string of XML data!"
        sys.exit(1)
        pass

    rootNode = dom.documentElement
    return walk(rootNode)
## END parseXml

if __name__ == '__main__':
    nodemap = parseXml('/home/kshuk/xmltest.txt')
    pprint.pprint(nodemap)

