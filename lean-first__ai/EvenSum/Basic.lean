-- Definition: a number is even if there exists some k such that n = 2 * k
def Even (n : Nat) : Prop := ∃ k : Nat, n = 2 * k

-- Theorem: the sum of two even numbers is even
theorem even_add_even (m n : Nat) (hm : Even m) (hn : Even n) : Even (m + n) := by
  obtain ⟨k, hk⟩ := hm
  obtain ⟨j, hj⟩ := hn
  exact ⟨k + j, by rw [hk, hj]; omega⟩
