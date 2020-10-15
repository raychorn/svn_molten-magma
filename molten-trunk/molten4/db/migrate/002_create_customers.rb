class CreateCustomers < ActiveRecord::Migration
  def self.up 
      #remove_column :customer, :salary          
      #add_column :customer, :salary, :string    
  end

  def self.down   
    #add_column :customer, :salary, :string 
    #remove_column :customer, :salary        
  end
end
