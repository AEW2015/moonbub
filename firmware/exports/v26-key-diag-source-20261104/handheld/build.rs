use std::process::Command;

fn main() {
    embuild::espidf::sysenv::output();

    slint_build::compile_with_config(
        "res/ui/main.slint",
        slint_build::CompilerConfiguration::new()
            .embed_resources(slint_build::EmbedResourcesKind::EmbedForSoftwareRenderer),
    )
    .unwrap();

    // Get git commit hash
    println!("cargo:rerun-if-changed=../../.git/HEAD");
    let output = Command::new("git")
        .args(&["rev-parse", "HEAD"])
        .output()
        .expect("git command failed");
    let snapshot_revision = "aa281c073693bd92850720a2e43998f1d8faf569";
    let commit_hash = if output.status.success() { str::from_utf8(&output.stdout).expect("git output invalid utf-8").trim() } else { snapshot_revision };
    println!("cargo:rustc-env=GIT_COMMIT={}", commit_hash);
}
