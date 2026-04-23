# EvenSum

A first Lean 4 project formalizing the theorem: **the sum of two even numbers is even**.

## Setup

### Prerequisites

Install [elan](https://github.com/leanprover/elan) (Lean version manager):

```bash
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
```

### Build

```bash
lake build
```

### Run

```bash
lake exe evensum
```

## Project Structure

```
EvenSum/
  Basic.lean      -- Even definition + theorem statement
EvenSum.lean       -- Library root (imports modules)
Main.lean          -- Executable entry point
lakefile.toml      -- Lake build config
lean-toolchain     -- Lean version (v4.29.0)
```

## The Theorem

We define evenness from first principles and state the theorem with `sorry` as a placeholder for the proof:

```lean
def Even (n : Nat) : Prop := ∃ k : Nat, n = 2 * k

theorem even_add_even (m n : Nat) (hm : Even m) (hn : Even n) : Even (m + n) := by
  sorry
```

## How Verification Works

The real verification happens at build time. When `lake build` succeeds with no `sorry` warnings, that means Lean's type checker accepted the proof as valid. The executable is just a cosmetic entry point; Lean proofs don't "run" at runtime -- they're checked at compile time.

## Resources

- [Lean 4 documentation](https://lean-lang.org/lean4/doc/)
- [Lean community](https://leanprover-community.github.io/)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Mathematics in Lean](https://leanprover-community.github.io/mathematics_in_lean/)
