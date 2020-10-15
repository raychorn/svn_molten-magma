module ActiveRecord
  module Acts #:nodoc:
    module Viewable #:nodoc:
      def self.included(base)
        base.extend(ClassMethods)  
      end
      
      module ClassMethods
          def acts_as_viewable(options = {})

            has_many :viewings, :as => :viewable, :dependent => :destroy

            include ActiveRecord::Acts::Viewable::InstanceMethods
            extend ActiveRecord::Acts::Viewable::SingletonMethods          
          end
          
          # Returns the record and adds a viewing. If the record has a +views+ method
          # that counts the number of views, this is incremented.
          def view(id,contact)
            record = find(:first, :conditions => ["sf_id LIKE ?", "#{id}%"])
            raise ActiveRecord::RecordNotFound if record.nil?
            viewing = record.viewings.create!(:viewable => record, :sfcontact => contact)
            if record.respond_to?(:views) and record.respond_to?(:settings) and !record.settings.nil?
              record.settings.increment!(:views) 
            end
            return record
          end
          
          # Returns the most viewed records.
          def find_popular(limit = AppConstants::MOST_POPULAR_LIMIT)
            return [] unless self.new.respond_to?(:views)
            conditions = if self.to_s == 'Sfsolution'
                            "status = '#{Sfsolution::STATUSES[:published]}'"
                         else
                           ""
                         end
            records = self.new.build_settings.class.find(:all, :order => "views DESC", :limit => limit).map do |setting| 
              setting.send(self.new.class.to_s.underscore)
            end
            records.reject { |record| record.is_a?(Sfsolution) and !record.published? }.compact
          end
      end
      
      module SingletonMethods
      end
      
      module InstanceMethods
        
      end # InstanceMethods
    end # Viewable
  end # Acts
end # ActiveRecord