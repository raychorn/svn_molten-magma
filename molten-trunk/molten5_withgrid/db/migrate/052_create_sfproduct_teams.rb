class CreateSfproductTeams < ActiveRecord::Migration
  def self.up
    create_table :sfproduct_team do |t|
      t.column :sf_id, :string
    end
    SalesforceSync.update_schema
  end

  def self.down
    drop_table :sfproduct_team
  end
end
