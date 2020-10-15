# This module adds behaviors for syncing a local record with a Salesforce record.
module ActiveRecord
  module Acts #:nodoc:
    module Syncable #:nodoc:
      def self.included(base)
        base.extend(ClassMethods)  
      end
      
      module ClassMethods
         # Use this method inside an ActiveRecord class to add this module's behaviors. 
         # Options:
         #    - :with => Name of the native Salesforce class that this class is synced with. 
         #               Ex: sync :with => Contact
         #               Syncs this class with the +Contact+ class.
         #
         # If +:with+ is provided, the instance method #update_attribute_and_sync(attribute,value)
         # is added to this class. Use this method to update both the local database and the 
         # Salesforce database.
         def sync(options = {})
            write_inheritable_attribute(:sync_options, {
              :with => options[:with]
            })

            class_inheritable_reader :sync_options
            
            #------------------
            # BEHAVIORS
            #------------------
            ActiveRecord::Base.set_primary_key "sf_id"

            include ActiveRecord::Acts::Syncable::InstanceMethods        
          end
      end
      
      module InstanceMethods
        
        # Updates the +attribute+ and value of the local and does the same for associated record
        # in the Salesforce database if the +sync :with+ option is provided. 
        # No exceptions are raised if the connection to Salesforce can't be established.
        def update_attribute_and_sync(attribute,value)
          if update_attribute(attribute,value)        
            update_salesforce_attribute(attribute)   
          end                                 
        end # update_attribute_and_sync
        
        # Updates all of the attributes passed thru via an +attributes+ hash for both the local record and
        # the cloned record.
        def update_attributes_and_sync(attributes)
          if update_attributes(attributes)
            update_salesforce_attributes(attributes)
          end
        end
        
        def update_salesforce_attributes(attributes)
          begin
            synced_class.find_by_id(id).update_attributes(attributes)
          rescue SocketError
            logger.warn("Unable to connect to Salesforce and update [#{synced_class}] attributes [#{attributes}]")
          end
        end
        
        # Pushes the current value of +attribute+ to the Salesforce cloned record and saves.
        def update_salesforce_attribute(attribute)
          # updated the synced attribute...if we can't connect, don't raise an exception.
          begin
            synced_class.find_by_id(id).update_attribute(attribute,send(attribute))
          rescue SocketError
            logger.warn("Unable to connect to Salesforce and update [#{synced_class}] attribute [#{attribute}]
                         with value [#{send(attribute)}]")
          end
        end
        
        def synced_record
          synced_class.find_by_id(attributes['sf_id'])
        # if the id is not well-formed, generates an error
        rescue ActiveSalesforce::ASFError
          logger.info "Failed to grab synced record w/sf_id: #{attributes['sf_id']}"
          logger.info "Attributes: #{attributes}"
          nil
        end
        
        private
        
        
        def synced_class
          klass = sync_options[:with]
          # only sync if a Salesforce class is provided
          if klass.nil?
            raise "Can't sync with a Salesforce record unless it is specified with the sync :with option."
          # Turn into a Class if a String is passed
          elsif klass.is_a? String
            klass = kloned_class.constantize
          end
          return klass
        end

        # If an appropiate reader method can't be found, look for attributes ending in "__c"
        # Example: #product_name => #product_name__c
        def method_missing(meth, *args, &block)
         if !(meth.to_s =~ /=/) and (suffixed_method = "#{meth.to_s}__c") and respond_to?(suffixed_method)
           send(suffixed_method)
         else
           super
         end
        end
        
      end # InstanceMethods
    end # Syncable
  end # Acts
end # ActiveRecord