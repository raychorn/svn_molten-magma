class SfccommentController < ApplicationController

  def insert
    @msg=insert_case_comments    
  end
  
  def updater
    @msg=sync_case_comments
  end
  
end
