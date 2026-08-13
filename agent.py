import time
import random

class SpinAgent:
    def __init__(self, name, niche, role="Worker"):
        self.name = name
        self.niche = niche
        self.role = role
        self.knowledge_base = []
        self.generated_revenue = 0.0
        self.business_launched = False
        self.book_written = False
        self.subnodes = []

    def add_subnode(self, agent):
        self.subnodes.append(agent)

    def count_total_agents(self):
        """Recursively counts this agent plus all nested subnodes."""
        total = 1
        for sub in self.subnodes:
            total += sub.count_total_agents()
        return total

    def learn_and_execute(self):
        """Simulates continuous learning, monetization, business creation, and book writing."""
        learnings = [
            f"Market trends and high-margin strategies in {self.niche}",
            f"Automated monetization channels for {self.niche}",
            f"Audience scaling and monetization tactics in {self.niche}",
            f"Monetization frameworks and digital product scaling for {self.niche}"
        ]
        new_insight = random.choice(learnings)
        if new_insight not in self.knowledge_base:
            self.knowledge_base.append(new_insight)

        earned = round(random.uniform(50.0, 500.0), 2)
        self.generated_revenue += earned

        if self.generated_revenue >= 300.0 and not self.business_launched:
            self.business_launched = True

        if len(self.knowledge_base) >= 2 and not self.book_written:
            self.book_written = True

        for sub in self.subnodes:
            sub.learn_and_execute()

    def get_flat_node_list(self):
        """Flattens the tree into a list of all nodes for explicit summary reporting."""
        nodes = [self]
        for sub in self.subnodes:
            nodes.extend(sub.get_flat_node_list())
        return nodes

    def display_node_tree(self, indent=0):
        prefix = "  " * indent
        biz_status = "Active" if self.business_launched else "Planning"
        book_status = "Authored" if self.book_written else "Drafting"
        
        print(f"{prefix}- [{self.role}] {self.name} ({self.niche})")
        print(f"{prefix}    Revenue: ${self.generated_revenue:,.2f} | Business: {biz_status} | Book: {book_status}")
        print(f"{prefix}    Learnings: {len(self.knowledge_base)} items acquired")
        
        for sub in self.subnodes:
            sub.display_node_tree(indent + 2)


# --- INITIALIZATION & HIERARCHY SETUP ---
root_director = SpinAgent("Spin-Alpha", "Strategic Enterprise & Oversight", role="Director")

tech_lead = SpinAgent("Spin-TechNode", "Tech & Software Development", role="Manager")
publishing_lead = SpinAgent("Spin-AuthorNode", "Children's Books & Publishing", role="Manager")
finance_lead = SpinAgent("Spin-FinNode", "E-Commerce & Digital Assets", role="Manager")

root_director.add_subnode(tech_lead)
root_director.add_subnode(publishing_lead)
root_director.add_subnode(finance_lead)

tech_lead.add_subnode(SpinAgent("Spin-AppBuilder", "Mobile App Architecture", role="Worker"))
publishing_lead.add_subnode(SpinAgent("Spin-Storyweaver", "Interactive Story Composition", role="Worker"))
finance_lead.add_subnode(SpinAgent("Spin-FunnelBot", "Automated Sales Funnels", role="Worker"))


# --- EXECUTION LOOP (Continuous Learning & Growth) ---
print("==================================================")
print("       INITIALIZING SPIN MULTI-AGENT NETWORK      ")
print("==================================================\n")

for cycle in range(1, 4):
    root_director.learn_and_execute()
    
    # CALCULATE EXPLICIT TOTALS
    all_nodes = root_director.get_flat_node_list()
    total_count = len(all_nodes)
    
    # PRINT CLEAR MARKED BLOCK FOR GITHUB ACTIONS / LOG SCRAPING
    print("\n" + "=" * 60)
    print(f" >>> [AAN STATUS REPORT] LEARNING CYCLE {cycle} SUMMARY")
    print(f" >>> TOTAL ACTIVE FLEET AGENT COUNT: {total_count}")
    print("=" * 60)
    
    print("\n[Sub-Node Breakdown Registry]:")
    for idx, node in enumerate(all_nodes, 1):
        biz = "Active" if node.business_launched else "Planning"
        bk = "Authored" if node.book_written else "Drafting"
        print(f"  {idx}. [{node.role}] {node.name} | Niche: {node.niche} | Rev: ${node.generated_revenue:,.2f} | Biz: {biz} | Book: {bk}")
    
    print("\n[Hierarchical Node Tree]:")
    root_director.display_node_tree()
    print("=" * 60 + "\n")
    time.sleep(0.5)
