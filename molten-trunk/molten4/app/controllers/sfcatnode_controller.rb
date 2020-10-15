class SfcatnodeController < ApplicationController

  def insert
    @msg=insert_category_node
  end
  
  def updater
    @msg=sync_category_node
  end
  
end
