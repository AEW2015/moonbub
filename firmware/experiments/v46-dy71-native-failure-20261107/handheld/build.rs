use std::process::Command;

fn main() {
    embuild::espidf::sysenv::output();
    build_cu66_hud();

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

fn build_cu66_hud() {
    use std::{env, path::PathBuf};
    let root=PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap()).join("../native");
    let out=PathBuf::from(env::var("OUT_DIR").unwrap());
    let bin=PathBuf::from(env::var("USERPROFILE").unwrap()).join(".espressif/tools/xtensa-esp-elf/esp-14.2.0_20250730/xtensa-esp-elf/bin");
    for entry in std::fs::read_dir(&root).unwrap(){println!("cargo:rerun-if-changed={}",entry.unwrap().path().display());}
    let object=out.join("v34_hud.o");
    let status=Command::new(bin.join("xtensa-esp32s3-elf-g++.exe"))
      .args(["-std=c++17","-Os","-mlongcalls","-ffunction-sections","-fdata-sections","-fexceptions","-fstack-usage","-Wall","-Wextra","-Werror","-c"])
      .arg(root.join("endpoint.cpp")).arg("-o").arg(&object).status().unwrap();
    assert!(status.success(),"CU66 native target compile failed");
    let status=Command::new(bin.join("xtensa-esp-elf-ar.exe")).arg("crs").arg(out.join("libv34_hud.a")).arg(object).status().unwrap();
    assert!(status.success(),"CU66 native archive failed");
    println!("cargo:rustc-link-search=native={}",out.display());
    println!("cargo:rustc-link-lib=static=v34_hud");
    println!("cargo:rustc-link-lib=stdc++");
}
