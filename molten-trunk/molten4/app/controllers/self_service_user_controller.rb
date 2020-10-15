class SelfServiceUserController < ApplicationController
def list
	@acct=SelfServiceUser.columns
	#@sfaccts=CategotyData.find_all
  end
end
