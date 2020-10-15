class CategoryDataController < ApplicationController

  def list
	@acct=CategoryData.columns
	#@sfaccts=CategotyData.find_all
  end
end
