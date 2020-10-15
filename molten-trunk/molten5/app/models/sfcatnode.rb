class Sfcatnode < ActiveRecord::Base
  sync :with => "CategoryNode"
  set_primary_key "sf_id"
  #------------------
  # BEHAVIORS
  #------------------
  acts_as_tree :foreign_key => "parent_id", :order => "master_label"
  has_many :solutions, :through => :category_datas, :order => "solution_name", 
           :conditions => "status = '#{Sfsolution::STATUSES[:published]}'"
  has_many :category_datas, :class_name => "Sfcatdata", :foreign_key => 'category_node_id'
  include SolutionViewing
  
  #------------------
  # CLASS METHODS
  #------------------
  
  # Returns all top-level category nodes. These are nodes under 'Public Molten Categories'.
  def self.top_level
    return [] unless root
    find(:all,:conditions => "parent_id = '#{root.id}'", :order => 'master_label')
  end
  
  def self.root
    find_by_sf_id('02n300000000KDTAA2') || find(:first)
  end
  
  #------------------
  # INSTANCE METHODS
  #------------------
  
  # Finds solutions for the +contact+. The contact's email address must end in 
  # 'molten-magma' or 'highgroove' to view the solution if
  # it's status is not 'Published'.
  def solutions_for_contact(contact)
    condition = set_solution_viewable_status_for_contact(contact)
                 
    solutions.find(:all, :include => [:settings], 
                   :order => "sfsolution_setting.relevancy DESC", 
                   :conditions => condition)
  end
  
  # Overwrites the root category's name to display "All Categories".
  def name
    if id == Sfcatnode.root.id
      "All Categories"
    else
      read_attribute('master_label')
    end
  end
end
