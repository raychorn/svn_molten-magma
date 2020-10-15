class CaseCommentController < ApplicationController

def list
	@acct=CaseComment.columns
	@sfaccts=CaseComment.find_all
  end 
  
end
