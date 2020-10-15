#!/bin/env python2.3
"""
Class and tool to assist in the creation and manipulation of Notes
"""

from sfConstant import *
from sfMagma import *

class SFNote(SFMagmaEntity):
    def __init__(self, entity=None, data={}, action=None, sfTool=None,
                 debug=0):
        """
        If an active tool object is not passed in then a connection is created.
        """

        if entity is None:
            entity = NOTE_OBJ

        if sfTool is None:
            sfTool = SFNoteTool()

        SFEntityBase.__init__(self, entity, data=data, action=action,
                              sfTool=sfTool, debug=debug)
        return
    ## END __init__

class SFNoteTool(SFMagmaTool):

    def findNote(self, parentSfId, title):
        """
        Try to find a note attached to the entity with parentSfId and
        having title.

        Return a note object if found, None if not.
        """
        where = [['ParentId', '=', parentSfId], 'and',
                 ['Title', '=', title]]
        queryList = self.query(NOTE_OBJ, where=where, sc='all')

        if queryList in BAD_INFO_LIST:
            note = None
            msg = "findNote: NO Note found with parent %s and title %s" \
                  %(parentSfId, title)
            self.setLog(msg, 'debug')

        else:
            if len(queryList) > 1:
                # Hrm, more than one note matches
                msg = "findNote: More than one note found with parent %s and title %s" %(parentSfId, title)
                self.setLog(msg, 'warn')

            noteInfo = queryList[0]
            noteData = {NOTE_OBJ: noteInfo}

            note = SFNote(data=noteData, sfTool=self)
            pass

        return note
    ## END findNote

    def retrieveNote(self, noteId):
        """
        Given a noteID, return the note object for that note
        """
        note = None
        if noteId not in [None, '']:
            ret = self.retrieve([noteId], NOTE_OBJ)
        
            if ret in BAD_INFO_LIST:
                msg = "retrieveNote: Couldn't retrieve note with id %s" %noteId
                self.setLog(msg, 'error')
            else:
                # success!
                noteData = {NOTE_OBJ: ret[0]}
                note = SFNote(NOTE_OBJ, data=noteData, sfTool=self)
                pass
        else:
            msg = "retrieveNote: invalid NoteId: '%s'" %noteId
            self.setLog(msg, 'error')    

        return note
    ## END retrieveNote
        
    def createNote(self, parentSfId, title, body, isPrivate=False,
                   ownerId=None):
        """
        Create a Note with given title and body attached to provided ID
        Return SFnote id
        """
            
        noteInfo = {'Title': title,
                    'Body': body,
                    'ParentId': parentSfId,
                    'IsPrivate': isPrivate}

        if ownerId is not None:
            noteInfo['OwnerId'] = ownerId

        noteId = self.create(NOTE_OBJ, [noteInfo])

        note = None

        if noteId in BAD_INFO_LIST:
            msg = "createNote: Note creation on parent entity id %s failed" \
                  %parentSfId
            self.setLog(msg, 'error')
            
        return noteId
    ## END createNote
