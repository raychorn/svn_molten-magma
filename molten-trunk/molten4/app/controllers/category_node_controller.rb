class CategoryNodeController < ApplicationController

def list
	@acct=CategoryNode.columns
	
	#@sfaccts=CategotyData.find_all
  end
end
