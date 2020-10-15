class AddIndexes < ActiveRecord::Migration
  def self.up
    add_index :sfcontact, :sf_id
    add_index :sfcase, :contact_id
    add_index :sfsolution, :sf_id
    add_index :viewing, :sfcontact_id
    add_index :viewing, :viewable_type
    add_index :sfaccount, :sf_id
    add_index :sfuser, :sf_id
    add_index :sfattach, :parent_id
    add_index :sfccomment, :parent_id
    add_index :sfcontact_setting, :sfcontact_id
    add_index :sfcase, :sf_id
    add_index :sfcatnode, :sf_id
    add_index :sfcatdata, :category_node_id
    add_index :sfcatdata, :related_sobject_id
    add_index :sfcatnode, :parent_id
  end

  def self.down
    remove_index :sfcontact, :sf_id
    remove_index :sfcase, :contact_id
    remove_index :sfsolution, :sf_id
    remove_index :viewing, :sfcontact_id
    remove_index :viewing, :viewable_type
    remove_index :sfaccount, :sf_id
    remove_index :sfuser, :sf_id
    remove_index :sfattach, :parent_id
    remove_index :sfccomment, :parent_id
    remove_index :sfcontact_setting, :sfcontact_id
    remove_index :sfcase, :sf_id
    remove_index :sfcatnode, :sf_id
    remove_index :sfcatdata, :category_node_id
    remove_index :sfcatdata, :related_sobject_id
    remove_index :sfcatnode, :parent_id
  end
end
