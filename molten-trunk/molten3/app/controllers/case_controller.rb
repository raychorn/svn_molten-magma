class CaseController < ApplicationController

  def list
	@cse=Case.columns
	@sfcse=Case.find(:all, :limit => 60000)

  end
end
