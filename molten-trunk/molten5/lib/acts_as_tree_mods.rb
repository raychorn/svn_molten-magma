module ActiveRecord
  module Acts #:nodoc:
    module Tree #:nodoc:
      module InstanceMethods
        # Prevents infinite recursion
        def ancestors
          node, nodes = self, []
          nodes << node = node.parent while (node.parent && !nodes.include?(node.parent))
          nodes
        end
      end
    end
  end
end
