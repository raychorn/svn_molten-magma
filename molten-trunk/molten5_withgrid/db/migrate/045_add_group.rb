class AddGroup < ActiveRecord::Migration
  def self.up
    create_table :sfgroup do |t|
      t.column :sf_id, :string
    end
  end

  def self.down
    drop_table :sfgroup
  end
end