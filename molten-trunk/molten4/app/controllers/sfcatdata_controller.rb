class SfcatdataController < ApplicationController

  def insert
    @msg=insert_category_data    
  end
  
  def updater
    @msg=sync_category_data
  end
  
end
