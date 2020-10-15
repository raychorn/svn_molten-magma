class CreateSfsolutionSettings < ActiveRecord::Migration
  def self.up
    create_table :sfsolution_setting do |t|
      t.column :sfsolution_id, :string
      t.column :views, :integer, :default => 0
    end
  end

  def self.down
    drop_table :sfsolution_setting
  end
end
